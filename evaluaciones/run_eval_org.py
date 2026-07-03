from __future__ import annotations

from evaluaciones.run_eval import main


if __name__ == "__main__":
    import sys

    sys.argv[1:1] = ["--retriever", "org"]
    main()