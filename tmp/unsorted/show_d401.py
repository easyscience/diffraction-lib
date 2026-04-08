files_lines = [
    ('src/easydiffraction/analysis/calculators/crysfml.py', [108,160,205]),
    ('src/easydiffraction/analysis/calculators/cryspy.py', [357,377]),
    ('src/easydiffraction/analysis/calculators/pdffit.py', [61]),
    ('src/easydiffraction/analysis/minimizers/dfols.py', [55,77]),
    ('src/easydiffraction/analysis/minimizers/lmfit.py', [40,66,96,117,140]),
    ('src/easydiffraction/core/singleton.py', [28,45,49,65,107,116,138]),
    ('src/easydiffraction/core/variable.py', [386]),
    ('src/easydiffraction/datablocks/experiment/categories/data/bragg_pd.py', [312,317,329,334,339,344,494,567]),
    ('src/easydiffraction/datablocks/experiment/categories/data/bragg_sc.py', [268,286,291,301,308,313,318]),
    ('src/easydiffraction/datablocks/experiment/categories/data/total_pd.py', [195,200,212,217,340]),
    ('src/easydiffraction/project/project_info.py', [119]),
    ('src/easydiffraction/utils/environment.py', [35,47]),
    ('src/easydiffraction/utils/logging.py', [685]),
    ('src/easydiffraction/utils/utils.py', [308]),
]
for fname, lines in files_lines:
    with open(fname) as f:
        content = f.readlines()
    for ln in lines:
        lo = max(0, ln-2)
        hi = min(len(content), ln+2)
        for i, l in enumerate(content[lo:hi]):
            print(f'{fname}:{lo+i+1}: {l}', end='')
        print('---')

