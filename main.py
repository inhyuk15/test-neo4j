

# from src.cst_gen2 import get_call_graph_with_cfg
from src.cst_gen import get_call_graph_with_cfg
from src.graphdb2 import test2
from src.graphdb1 import test
from src.cst_gen1 import test3

def main():
    get_call_graph_with_cfg()
    # test3()
    # test2()
    # test()


if __name__ == "__main__":
    main()
