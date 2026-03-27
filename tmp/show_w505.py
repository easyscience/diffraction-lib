files_lines = [
    ('src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py', [196,277,324,527,602]),
    ('src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py', [29,298,422]),
    ('src/easydiffraction/datablocks/experiment/categories/data/total_pd.py', [207]),
    ('src/easydiffraction/datablocks/experiment/categories/experiment_type/default.py', [30]),
    ('src/easydiffraction/datablocks/experiment/categories/extinction/shelx.py', [20]),
    ('src/easydiffraction/datablocks/experiment/item/base.py', [71,604]),
    ('src/easydiffraction/datablocks/experiment/item/factory.py', [78]),
    ('src/easydiffraction/datablocks/structure/item/base.py', [248]),
    ('src/easydiffraction/display/base.py', [144]),
    ('src/easydiffraction/display/utils.py', [21]),
    ('src/easydiffraction/io/cif/serialize.py', [162]),
    ('src/easydiffraction/project/project.py', [78]),
    ('src/easydiffraction/summary/summary.py', [208]),
    ('src/easydiffraction/utils/logging.py', [327,478]),
    ('src/easydiffraction/utils/utils.py', [52,73]),
]
for fname, lines in files_lines:
    with open(fname) as f:
        content = f.readlines()
    for ln in lines:
        lo = max(0, ln-2)
        hi = min(len(content), ln+1)
        for i, l in enumerate(content[lo:hi]):
            print(f'{fname}:{lo+i+1}: {l}', end='')
        print('---')

