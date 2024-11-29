import read_file

if __name__ == "__main__":
    opeations = read_file.get_operations(
        "displib_instances_testing/displib_testinstances_headway1.json")
    print(*opeations.items(), sep="\n")
