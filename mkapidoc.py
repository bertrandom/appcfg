import re

from doc2md import mod2md

import appcfg

doc = mod2md(appcfg, "", "API", toc=False)
doc = doc[6 : doc.find("### __version__") - 1]


with open("readme.md", "r+") as f:
    md = f.read()
    md = re.sub(
        r"<!-- BEING API DOC -->.+<!-- END API DOC -->",
        "<!-- BEING API DOC -->" + doc + "<!-- END API DOC -->",
        md,
        flags=re.DOTALL,
    )

    f.seek(0)
    f.write(md)
