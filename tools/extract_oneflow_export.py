# python3 -m pip install isort autoflake astpretty
# requires python3.8 to run
import os
import argparse
import ast
from posixpath import basename, relpath
import subprocess
import multiprocessing
from pathlib import Path, PurePosixPath
from functools import partial
from collections import OrderedDict
import astpretty
import sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "--out_dir", type=str, default="python",
)
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--debug", "-d", action="store_true")
parser.add_argument("--skip_autoflake", "-sa", action="store_true")
parser.add_argument("--skip_black", "-sb", action="store_true")
args = parser.parse_args()
assert args.out_dir
assert args.out_dir != "~"
assert args.out_dir != "/"
OUT_PATH = Path(args.out_dir)


def dumpprint(node):
    astpretty.pprint(node)


def is_export_decorator(d):
    return (
        isinstance(d, ast.Call)
        and isinstance(d.func, ast.Name)
        and d.func.id == "oneflow_export"
    )


def get_parent_module(value):
    return ".".join(value.split(".")[0:-1])


def join_module(parent, child):
    if child:
        return ".".join([parent, child])
    else:
        return parent


def path_from_module(module, is_init=False):
    if is_init:
        return Path("/".join(module.split(".") + ["__init__.py"]))
    else:
        return Path("/".join(module.split(".")) + ".py")


def module_from_path(path: Path):
    assert path.name.endswith(".py")
    parts = path.parts
    if parts[-1] == "__init__.py":
        return ".".join(path.parts[0:-1])
    else:
        return ".".join(path.parts)[0:-3]


class ExportVisitor(ast.NodeTransformer):
    def __init__(self, root_module="oneflow") -> None:
        super().__init__()
        self.staging_decorators = []
        self.root_module = root_module
        self.export_modules = {}

    def append_export(self, target_module=None, node=None):
        if target_module not in self.export_modules:
            module = ast.Module(body=[], type_ignores=[])
            self.export_modules[target_module] = module
        else:
            module = self.export_modules[target_module]
        # dumpprint(module)
        module.body.append(node)

    def visit_ImportFrom(self, node):
        if not node.module:
            dumpprint(node)
        if node.module:
            if node.module == "__future__" or node.module.startswith(
                "oneflow.python.oneflow_export"
            ):
                return None
            if node.module.startswith("oneflow.python"):
                node.module = node.module.replace("oneflow.python", "oneflow")
                return node
        return node

    def visit_alias(self, node: ast.alias) -> ast.alias:
        if node.name.startswith("oneflow.python"):
            node.name = node.name.replace("oneflow.python", "oneflow")
            return node
        else:
            return node

    def visit_ClassDef(self, node):
        return self.visit_FunctionDef(node)

    def visit_FunctionDef(self, node):
        for d in node.decorator_list:
            if is_export_decorator(d):
                import_from_exports = []
                target_module = None
                target_name = None
                for (i, arg) in enumerate(d.args):
                    if i == 0:
                        target_module = join_module(
                            self.root_module, get_parent_module(arg.value)
                        )
                        target_name = arg.value.split(".")[-1]
                    asname = None
                    if node.name != target_name:
                        asname = node.name
                    import_from_export = ast.ImportFrom(
                        module=target_module,
                        names=[ast.alias(name=target_name, asname=asname),],
                        level=0,
                    )
                    import_from_exports.append(import_from_export)
                self.append_export(target_module=target_module, node=node)
                return import_from_exports
        return node


class SrcFile:
    def __init__(self, spec) -> None:
        is_test = "is_test" in spec and spec["is_test"]
        self.export_visitor = None
        self.tree = None
        self.dst = Path(spec["dst"])
        if is_test and args.verbose:
            print("[skip test]", spec["src"])
        else:
            txt = spec["src"].read_text()
            self.tree = ast.parse(txt)
            root_module = "oneflow"
            if "compatible_single_client_python" in spec["src"].parts:
                root_module = "oneflow.compatible.single_client"
            self.export_visitor = ExportVisitor(root_module=root_module)
            self.export_visitor.visit(self.tree)


def get_specs_under_python(python_path=None, dst_path=None):
    specs = []
    for p in Path(python_path).rglob("*.py"):
        rel = p.relative_to(python_path)
        dst = Path(dst_path).joinpath(rel)
        spec = {"src": p, "dst": dst}
        if rel.parts[0] == "test":
            spec["is_test"] = True
        specs.append(spec)
    return specs


def get_files():
    srcs = (
        get_specs_under_python(python_path="oneflow/python", dst_path="oneflow")
        + get_specs_under_python(
            python_path="oneflow/compatible_single_client_python",
            dst_path="oneflow/compatible/single_client",
        )
        + [
            {"src": Path("oneflow/init.py"), "dst": "oneflow/__init__.py"},
            {"src": Path("oneflow/__main__.py"), "dst": "oneflow/__main__.py"},
            {
                "src": Path("oneflow/single_client_init.py"),
                "dst": "oneflow/compatible/single_client/__init__.py",
            },
            {
                "src": Path("oneflow/single_client_main.py"),
                "dst": "oneflow/compatible/single_client/__main__.py",
            },
        ]
    )
    srcs = list(filter(lambda x: ("oneflow_export" not in x["src"].name), srcs))
    if args.debug:
        srcs = [
            {
                "src": Path("oneflow/python/ops/nn_ops.py"),
                "dst": "oneflow/ops/nn_ops.py",
            },
            {
                "src": Path("oneflow/python/advanced/distribute_ops.py"),
                "dst": "oneflow/advanced/distribute_ops.py",
            },
        ]
    pool = multiprocessing.Pool()
    srcs = pool.map(SrcFile, srcs,)
    pool.close()
    return srcs


class ModuleNode:
    def __init__(self, name=None, parent=None) -> None:
        self.children = dict()
        self.parent = parent
        self.level = 0
        if parent:
            self.level = parent.level + 1
        self.name = name

    def add_or_get_child(self, name):
        if name in self.children:
            return self.children[name]
        else:
            self.children[name] = ModuleNode(name=name, parent=self)
            return self.children[name]

    @property
    def is_leaf(self):
        return len(self.children.keys()) == 0

    def walk(self, cb):
        cb(self)
        for child in self.children.values():
            child.walk(cb)

    @property
    def leafs(self):
        ret = []

        def add_leafs(node: ModuleNode):
            if node.is_leaf:
                print("[leaf]", node.full_name)
                print(node)
                ret.append(node)

        self.walk(add_leafs)
        return ret

    @property
    def full_name(self):
        current_parent = self
        ret = self.name
        while current_parent.parent:
            current_parent = current_parent.parent
            ret = current_parent.name + "." + ret
        return ret

    def __str__(self) -> str:
        return "\n".join(
            [f"{self.full_name}"]
            + [child.__str__() for child in self.children.values()]
        )


def save_trees(args=None):
    dst: Path = args["dst"]
    trees = args["trees"]
    # if len(trees) > 2:
    # print(dst, len(trees))
    dst_full = OUT_PATH.joinpath(dst)
    dst_full.parent.mkdir(parents=True, exist_ok=True)
    dst_full.touch()
    new_txt = "\n".join([ast.unparse(tree) for tree in trees])
    dst_full.write_text(new_txt)


if __name__ == "__main__":
    out_oneflow_dir = os.path.join(args.out_dir, "oneflow")
    subprocess.check_call(f"rm -rf {out_oneflow_dir}", shell=True)
    subprocess.check_call(f"mkdir -p {out_oneflow_dir}", shell=True)
    # step 0: parse and load all segs into memory
    srcs = get_files()
    final_trees = {}

    root_module = ModuleNode(name="oneflow")
    for s in srcs:
        # src
        target_module = module_from_path(s.dst)
        final_trees[target_module] = final_trees.get(target_module, [])
        final_trees[target_module].append(s.tree)
        # exports
        for export_path, export_tree in s.export_visitor.export_modules.items():
            final_trees[export_path] = final_trees.get(export_path, [])
            final_trees[export_path].append(export_tree)
            # build module tree
            parts = export_path.split(".")
            current_node = root_module
            assert current_node.name == parts[0]
            for part in parts[1::]:
                current_node = current_node.add_or_get_child(part)
    print(root_module)
    leaf_modules = set([leaf.full_name for leaf in root_module.leafs])
    pool = multiprocessing.Pool()

    def is_init(module):
        # if module in leaf_modules:
        #     print("[leaf]", module)
        # else:
        #     print("[not leaf]", module)
        return module not in leaf_modules

    srcs = pool.map(
        save_trees,
        [
            {"dst": path_from_module(module, is_init=is_init(module)), "trees": trees,}
            for module, trees in final_trees.items()
        ],
    )
    pool.close()
    # step 1: extract all exports
    # step 2: merge files under python/ into generated files
    # step 3: rename all
    # step 4: finalize __all__, if it is imported by another module or wrapped in 'oneflow.export', it should appears in __all__
    # step 5: save file and sort imports and format
    extra_arg = ""
    if args.verbose == False:
        extra_arg += "--quiet"
    if args.skip_autoflake == False:
        print("[postprocess]", "autoflake")
        subprocess.check_call(
            f"{sys.executable} -m autoflake --in-place --remove-all-unused-imports --recursive .",
            shell=True,
            cwd=args.out_dir,
        )
    print("[postprocess]", "isort")
    subprocess.check_call(
        f"{sys.executable} -m isort . {extra_arg}", shell=True, cwd=args.out_dir,
    )
    if args.skip_black == False:
        print("[postprocess]", "black")
        subprocess.check_call(
            f"{sys.executable} -m black . {extra_arg}", shell=True, cwd=args.out_dir,
        )
