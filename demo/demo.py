import string

import numpy as np
import pandas as pd

import dbrief.report

SEED = 43
rng = np.random.default_rng(seed=SEED)


def make_sample(size=(100, 4)):
    return pd.DataFrame(
        rng.lognormal(size=size), columns=list(string.ascii_lowercase[: size[-1]])
    )


if __name__ == "__main__":
    rpt = dbrief.report.Report(name="demo")

    for section in ["Section-1", "Section-2"]:
        rpt.add_section(title=section)
        for metric in ["Metric-A", "Metric-B"]:
            data = make_sample()
            rpt.add_figure(section=section, title=metric, data=data)

    rpt.to_html("demo-report.html")
