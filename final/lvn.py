import json
import sys
import random
import string

from utils.legacy.form_blocks import form_blocks
from utils.legacy.instr import is_commutative, get_args_list, get_dest


def check_dest_will_be_used_later(dest, instrs):
    for instr in instrs:
        if "dest" in instr and instr["dest"] == dest:
            return True
    return False


class LVNTable:
    def __init__(self):
        self.val2num = {}
        self.num2val = {}
        self.var2num = {}
        self.num2var = {}
        self.next_num = 0

    def get_new_num(self):
        num = self.next_num
        self.next_num += 1
        return num

    def get_num_by_value(self, value):
        return self.val2num.get(tuple(value))

    def get_num_by_var(self, var):
        return self.var2num.get(var)

    def set(self, num, value, var):
        self.val2num[tuple(value)] = num
        self.num2val[num] = value
        self.var2num[var] = num
        self.num2var[num] = var

    def set_var2num(self, num, var):
        self.var2num[var] = num

    def get_var_by_num(self, num):
        return self.num2var.get(num)

    def print(self):
        print("Value Number Table:")
        print("{:<10} {:<20} {:<10}".format("Num", "Value", "Variables"))
        for num in self.num2val:
            value = self.num2val[num]
            vars = [var for var, n in self.var2num.items() if n == num]
            print("{:<10} {:<20} {:<10}".format(num, str(value), ", ".join(vars)))


def local_value_numbering(fn):
    blocks = form_blocks(fn)

    for block in blocks:
        lvn_table = LVNTable()
        for i, inst in enumerate(block["instrs"]):
            if "op" not in inst or "funcs" in inst:
                continue
            if "type" in inst and inst["type"] == "float":
                continue
            if inst["op"] in ["alloc"]:
                continue

            args = [lvn_table.get_num_by_var(arg) for arg in get_args_list(inst)] + (
                [inst["value"]] if "value" in inst else []
            )
            if None in args:
                continue
            if is_commutative(inst):
                args.sort()

            value = [inst["op"]] + [
                str(arg) if isinstance(arg, bool) else arg for arg in args
            ]

            num = lvn_table.get_num_by_value(value)

            if num is not None:
                inst["op"] = "id"
                inst["args"] = [lvn_table.get_var_by_num(num)]
            else:
                num = lvn_table.get_new_num()
                if inst["op"] != "const":
                    inst["args"] = [lvn_table.get_var_by_num(m) for m in value[1:]]

                dest = get_dest(inst)
                if not dest:
                    continue
                if check_dest_will_be_used_later(dest, block["instrs"][i + 1 :]):
                    random_string = "".join(
                        random.choices(string.ascii_letters + string.digits, k=8)
                    )
                    new_dest = f"temp_{dest}_{random_string}"
                    for j in range(i + 1, len(block["instrs"])):
                        block["instrs"][j]["args"] = [
                            new_dest if arg == dest else arg
                            for arg in get_args_list(block["instrs"][j])
                        ]
                        if (
                            "dest" in block["instrs"][j]
                            and block["instrs"][j]["dest"] == dest
                        ):
                            break
                    inst["dest"] = new_dest

                lvn_table.set(num, value, inst["dest"])
            lvn_table.set_var2num(num, inst["dest"])
            # lvn_table.print()

    fn["instrs"] = [instr for block in blocks for instr in block["instrs"]]


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        local_value_numbering(fn)
    json.dump(prog, sys.stdout, indent=2)
