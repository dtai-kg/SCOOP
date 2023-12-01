import csv
import matplotlib

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.font_manager import FontProperties
import numpy as np
import statistics
import re

rml2shacl = 0.0
shaclgen = {}
with open('results.csv', 'r') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')

    # parse results in csv file and group them per size and shape
    firstrow = True
    for row in reader:
        # skip header row (there might be better ways to do this)
        if firstrow:
            firstrow = False
            continue

        tool_name = row[0]
        if tool_name == 'RML2SHACL':
            rml2shacl = statistics.mean([float(time) for time in row[1:]])

        size_searcher = re.search('SHACLGEN-([0-9]+)pc', tool_name)
        if size_searcher:
            size = int(size_searcher.group(1))

            # skip size 100, we want sizes 500 - 5000
            if size == 100:
                continue

            shaclgen[size] = statistics.mean([float(time) for time in row[1:]])

# ordering of measurements
x_axis = sorted(shaclgen.keys())
y_axis_shaclgen = [shaclgen[x] for x in x_axis]
y_axis_rml2shacl = [rml2shacl for x in x_axis]

# latex font
font = FontProperties(fname='OldStandardTT-Regular.ttf')

fig, ax = plt.subplots(1, 1, figsize=(3, 2))
plt.plot([x / 1000 for x in x_axis], y_axis_shaclgen, linewidth=0.75, color='black')
plt.plot([x / 1000 for x in x_axis], y_axis_rml2shacl, linewidth=0.75, color='black', linestyle='dashed')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
# ymin, ymax = ax.get_ylim()
# ax.set_ylim((ymin / 1.618, ymax))
# ax.text(1, 0.2, shape[6:-9], ha='right', va='bottom', transform=ax.transAxes, fontproperties=font)
for label in ax.get_yticklabels():
    label.set_fontproperties(font)
for label in ax.get_xticklabels():
    label.set_fontproperties(font)

plt.text(0.03, 0.5, "Execution time (seconds)", ha='center', va='center', transform=fig.transFigure, rotation=90,
         fontproperties=font)
plt.text(0.5, 0.04, "# products (thousands)", ha='center', va='center', transform=fig.transFigure,
         fontproperties=font)
plt.tight_layout()
plt.savefig("results.pdf")
plt.show()
