import re
t = open("campaign/s1-seeds-run.txt").read()
lines = [l for l in t.splitlines() if re.match(r"\[\d+\]", l)]
disc = sum(int(re.search(r": (\d+) disc", l).group(1)) for l in lines)
live = sum(len(re.findall(r"\('D\d+', '\w+'\)", l)) for l in lines)
withlive = sum(1 for l in lines if "live=[(" in l)
crash = sum(1 for l in lines if "crash" in l.lower())
print("programs", len(lines), "disc", disc, "live", live, "progs_with_live", withlive, "crash_lines", crash)
