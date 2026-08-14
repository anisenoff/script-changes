import matplotlib.pyplot as plt
import numpy as np
plt.rcParams['axes.prop_cycle'] = plt.cycler(color=["#77AADD", "#99DDFF", "#44BB99", "#BBCC33","#AAAA00","#EEDD88", "#EE8866","#FFAABB", "#DDDDDD"])
def quick_cdf(a, label=""):
    plt.plot(np.sort(a), np.linspace(0, 1, len(a), endpoint=False), drawstyle='steps-post', label = label)


def print_latex_fig_placeholder(filename):
    print(f"""\\begin{{figure}}[tb]
    \\centering
    \\includegraphics[width=\\linewidth]{{img/httparchive/{filename}}}
    \\caption{{\\todo{{{filename.replace('_', '\\_')}}}.}}
    \\label{{fig:{filename}}}
\\end{{figure}}""")
    
    
    
