import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from pandas import DataFrame
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import MultiComparison
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import matplotlib.pyplot as plt
from pymoo.factory import get_performance_indicator


def ANOVA(data):
    sns.set(style='darkgrid')
    fig, axes = plt.subplots(1, len(data))  # fig是整个画布，axes是子图,1，2表示1行两列
    fig.set_size_inches(10, 4)
    sns.set(font_scale=1)
    i = 0
    for key, df in data.items():
        print('-------------------------' + key + '---------------------------------')
        df_melt = pd.melt(df.reset_index(), id_vars=['index'])
        df_melt.columns = ['index', 'Levels', key]

        model = ols(key + ' ~ C(Levels)', data=df_melt).fit()
        anova_table = sm.stats.anova_lm(model, typ=1)
        print(anova_table)

        mc = MultiComparison(df_melt[key], df_melt['Levels'])
        tukey_result = mc.tukeyhsd(alpha=0.05)
        print(tukey_result)

        sns.boxplot(x='Levels', y=key, data=df_melt, ax=axes[i], width=0.40,
                    fliersize=2, linewidth=1)
        sns.swarmplot(x='Levels', y=key, data=df_melt, ax=axes[i])
        axes[i].set_xlabel('(' + chr(97 + i) + ')', y=-0.28, fontsize=13)
        axes[i].set_ylabel(key, fontsize=12)
        plt.subplots_adjust(wspace=0.20)
        axes[i].tick_params(labelsize=10)
        i = i + 1
    plt.show()


# minimal, a dominate b return 1, b dominate a return -1, else return 0
def dominates(a, b, maximise=False):
    if sum([a[i] == b[i] for i in range(len(a))]) == len(a):
        return 0

    if sum([a[i] >= b[i] for i in range(len(a))]) == len(a):
        if maximise:
            return 1
        else:
            return -1
    elif sum([a[i] <= b[i] for i in range(len(a))]) == len(a):
        if maximise:
            return -1
        else:
            return 1
    else:
        return 0


def find_pareto_frontier(candidates, is_show=False):
    # Sort on first dimension
    candidates = candidates[candidates[:, 0].argsort()]
    # Add first row to pareto_frontier
    pf = [candidates.tolist()[0]]
    # Test next row against the last row in pareto_frontier
    for c in candidates[1:, :]:
        can_join = True
        for x in pf:
            if dominates(x, c) > 0:
                can_join = False
        if not can_join:
            continue
        # pf = filter(lambda x: dominates(c, x) > 0, pf)
        pf = [x for x in pf if dominates(c, x) <= 0]
        pf.append(list(c))

    if is_show:
        pfx = np.array(pf)
        filter_arr = []
        for ee in candidates:
            mask1 = True
            for ss in pfx:
                mask2 = True
                for i in range(len(ss)):
                    if ee[i] != ss[i]:
                        mask2 = False
                        break
                if mask2:
                    mask1 = False
                    break
            filter_arr.append(mask1)
        ors = candidates[filter_arr]
        fig = plt.figure()
        ax = Axes3D(fig)
        ax.scatter(ors[:, 0], ors[:, 1], ors[:, 2], c='b', marker='o', s=40, alpha=1.0)
        ax.scatter(pfx[:, 0], pfx[:, 1], pfx[:, 2], c='r', marker='x', s=60, alpha=0.618)

        ax.set_xlabel('f1')
        ax.set_ylabel('f2')
        ax.set_zlabel('f3')
        plt.show()

    return pf


def get_mcpu_cvs():
    df_SLMODE = pd.read_excel(r"cpu.xlsx", sheet_name='SL-MODE')
    df_MODEns = pd.read_excel(r"cpu.xlsx", sheet_name='MODE-ns')
    df_MODEd = pd.read_excel(r"cpu.xlsx", sheet_name='MODE-d')

    df = pd.concat([df_SLMODE['SL-MODE'], df_MODEns['MODE/ns'], df_MODEd['MODE/d']], axis=1)

    return df


def calc_metric_cvs(instance_id):
    # 1. read the original  data
    df = pd.read_excel(r"pareto.xlsx", sheet_name=instance_id)
    data_alevt = {}
    data_event = {}
    for row_index, row in df.iterrows():
        alg = int(row['A'])
        evt = int(row['T'])
        flist1 = data_alevt.get((alg, evt), [])
        flist1.append([row['f1'], row['f2'], row['f3']])
        data_alevt[(alg, evt)] = flist1

        flist2 = data_event.get(evt, [])
        flist2.append([row['f1'], row['f2'], row['f3']])
        data_event[evt] = flist2
    # 2. obtain the Pareto Frontier of each event
    pf_event = {}
    ref_event = {}
    for key, value in data_event.items():
        pf = find_pareto_frontier(np.array(value))
        pf_event[key] = pf
        ref = np.array(value).max(axis=0)
        ref_event[key] = ref
    pf_alevt = {}
    for key, value in data_alevt.items():
        pf = find_pareto_frontier(np.array(value))
        pf_alevt[key] = pf

    # 3. calculate the mean of hv
    hv_data = {}
    for key, value in pf_alevt.items():
        algo = key[0]
        evnt = key[1]
        hvi = get_performance_indicator("hv", ref_point=np.array([1.0, 1.0, 1.0]))
        x = np.array(value)
        x_normed = x / (ref_event[evnt] + 1)
        hv = hvi.do(x_normed)
        if np.isnan(hv):
            hv = 0.1
        if algo not in hv_data.keys():
            hv_data[algo] = [hv]
        else:
            hv_data[algo] = hv_data[algo] + [hv]
    MHV_list = []
    for key, value in hv_data.items():
        tot = sum(value)
        mhv = tot / len(value)
        MHV_list.append(mhv)
        print(key, tot, mhv)

    # 4. calculate the mean of igd
    igd_data = {}
    for key, value in pf_alevt.items():
        algo = key[0]
        evnt = key[1]
        pf_normed = pf_event[evnt] / (ref_event[evnt] + 1)
        igdi = get_performance_indicator("igd", pf_normed)
        x_normed = np.array(value) / (ref_event[evnt] + 1)
        igd = igdi.do(x_normed)
        if np.isnan(igd):
            igd = 0.1
        if algo not in igd_data.keys():
            igd_data[algo] = [igd]
        else:
            igd_data[algo] = igd_data[algo] + [igd]
    MIGD_list = []
    for key, value in igd_data.items():
        tot = sum(value)
        migd = tot / len(value)
        MIGD_list.append(migd)
        print(key, tot, migd)
    return MHV_list, MIGD_list


if __name__ == "__main__":
    excl = pd.ExcelFile('pareto.xlsx')
    mhv_list = []
    migd_list = []
    mcpu_list = []
    for sheet in excl.sheet_names:
        print('------------------------', sheet, '-----------------------------')
        mhv, migd = calc_metric_cvs(sheet)
        mhv_list.append(mhv)
        migd_list.append(migd)
    df_mhv = pd.DataFrame(mhv_list, columns=['SL-MODE', 'MODE/ns', 'MODE/d'])
    df_migd = pd.DataFrame(migd_list, columns=['SL-MODE', 'MODE/ns', 'MODE/d'])
    df_cpu = get_mcpu_cvs()
    df_mhv.to_excel("mhv.xlsx")
    df_migd.to_excel("migd.xlsx")
    df_cpu.to_excel("mcpu.xlsx")

    ANOVA({'MHV': df_mhv, 'MIGD': df_migd, 'MCPU': df_cpu})
