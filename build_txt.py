import math
import re
from collections import defaultdict
from pathlib import Path

from py_dct_txt import DctTxtItem, DctTxtStore

from ori.the_large_dict.script.template import (
    EntryData,
    ExplainItemData,
    PosData,
    SenseData,
    Template,
)

EC_F = {
    "d": "过去式",
    "p": "过去分词",
    "i": "现在分词",
    "3": "第三人称单数",
    "r": "形容词比较级",
    "t": "形容词最高级",
    "s": "名词复数形式",
}

tag_paths = {
    "t4": "./ori/dict_data/tags/cet4.txt",
    "t6": "./ori/dict_data/tags/cet6.txt",
    "gre": "./ori/dict_data/tags/gre.txt",
    "hs": "./ori/dict_data/tags/high_school.txt",
    "t8": "./ori/dict_data/tags/tem8.txt",
    "ms": "./ori/dict_data/tags/middle_school.txt",
    "pe": "./ori/dict_data/tags/npee.txt",
    "ps": "./ori/dict_data/tags/primary_school.txt",
    "tf": "./ori/dict_data/tags/toefl.txt",
    # "of": "./ori/dict_data/tags/oxford_3000.txt",
}
tag_names = {
    "ps": "小学",
    "ms": "初中",
    "hs": "高中",
    "t4": "四级",
    "t6": "六级",
    "t8": "专八",
    "pe": "考研",
    "gre": "GRE",
    "tf": "托福",
}
tag_idxes = {t: i for i, t in enumerate(tag_names.keys())}
word_tags = defaultdict(set)
for tag, path in tag_paths.items():
    with open(path, "r", encoding="utf-8") as f:
        for w in f:
            word_tags[w.strip()].add(tag)
word_tags = dict(word_tags)


def remove_space(s: str):
    s = re.sub(r"\s*\n\s*", "\n", s)
    s = re.sub(r"[ \r\t\f\v]+", " ", s)
    return s.strip()


def split_pos(s: str) -> ExplainItemData | None:
    match = re.match(r"^([a-zA-Z0-9 ]+\.)?(.+)$", s)
    if match:
        pos = match.group(1)
        pos = pos.strip() if pos else ""
        return {"pos": pos, "v": match.group(2).strip()}
    print(f"dismatch : {s}")


def calc_pos_percent(kvs: dict) -> list[PosData]:
    if len(kvs) == 0:
        return []
    frqd: dict[str, int] = {part: v.get("frq", 0) for part, v in kvs.items()}
    total_frq = sum(frqd.values())
    total_percent = 100
    pos_data: list[PosData] = []

    for part, frq in sorted(frqd.items(), key=lambda pf: pf[1]):
        percent = math.ceil(frq / total_frq * 100)
        total_percent -= percent
        pos_data.append(
            {
                "pos": part,
                "percent": percent,
            }
        )
    if total_percent != 0:
        pos_data[-1]["percent"] += total_percent
    pos_data.reverse()
    return pos_data


def format_item(w: str, d: dict[str, DctTxtItem]):
    formatted: EntryData = {"title": w}
    other_data = {}
    explain = d.get("explain")
    if explain:
        formatted["explain"] = list(
            v for v in map(lambda s: split_pos(s), explain.l) if v
        )
    else:
        print(f"⚠️No explain :{w}")
        return

    phonetic = d.get("phonetic")
    if phonetic and phonetic.s:
        formatted["phonetic"] = phonetic.s

    collins = d.get("collins")
    if collins and type(collins.v) is int:
        formatted["cls_star_rate"] = collins.v
    elif collins:
        print(f"invalid {collins.v=}")

    bnc = d.get("bnc")
    if bnc and type(bnc.v) is int:
        formatted["bnc"] = int(bnc.v)
    elif bnc:
        print(f"invalid {bnc.v=}")

    freq = d.get("freq")
    if freq and type(freq.v) is int:
        formatted["frq"] = freq.v
    elif freq:
        print(f"invalid {freq.v=}")

    pos = d.get("pos")
    pos_data: list[PosData] = []
    if pos and len(pos.kvs):
        pos_data = calc_pos_percent(pos.kvs)
        other_data["pos"] = pos.kvs
    sense = d.get("sense_percent")
    sense_data: list[SenseData] = []
    if sense and len(sense.kvs):
        sense_items = sorted(sense.kvs.items(), key=lambda kv: kv[1], reverse=True)
        sense_data = [{"v": v, "percent": p} for v, p in sense_items]
    if pos_data or sense_data:
        formatted["percent"] = {
            "pos": pos_data,
            "sense": sense_data,
        }
    exchange = d.get("exchange")
    if exchange and len(exchange.kvs):
        eckvs = exchange.kvs
        ec = formatted["exchanges"] = []
        for f in "sdpi3rt":
            if f in eckvs:
                ec.append({"f": f, "v": eckvs[f]})
        if "f" in eckvs and "b" in eckvs:
            ec.append(
                {
                    "f": "desc",
                    "v": eckvs["b"]
                    + "的"
                    + (
                        "、".join(EC_F[f] for f in eckvs["f"][:-1]) + "和"
                        if len(eckvs["f"]) > 1
                        else ""
                    )
                    + EC_F[eckvs["f"][-1]],
                }
            )
    tags: list[str] = sorted(
        list(word_tags.get(w, [])), key=lambda t: tag_idxes.get(t, 100)
    )
    formatted["tags"] = [{"abbr": t, "v": tag_names.get(t, t)} for t in tags]

    lgk_id = d.get("lgk_id")
    if lgk_id and len(lgk_id.kvs):
        other_data["lgk_id"] = lgk_id.kvs

    formatted["json_data"] = other_data
    return formatted


def main():
    store = DctTxtStore()
    ori_gd = store.transpose_dict(store.load(Path("./ori/dict_data/data/")))
    my_dict_path = Path("./ori/my_dict_data/sense_data/")
    if my_dict_path.exists():
        ori_gd.update(store.transpose_dict(store.load(my_dict_path)))
    data_kd = store.transpose_dict({k: v for k, v in ori_gd.items() if k != "redirect"})

    t = Template(Path("./ori/the_large_dict/templates/entry.j2"))
    data = {}
    for w, d in data_kd.items():
        w = w.strip()
        entry_data = format_item(w, d)
        if entry_data:
            data[w] = t.render(entry_data)
    redirect = ori_gd.get("redirect", {})
    redirect_data = {
        k.strip(): v.s.strip()
        for k, v in redirect.items()
        if k.strip() not in data and v.s and v.s.strip()
    }
    path = Path("./temp/dict.txt")
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for k, v in data.items():
            content = remove_space(f"""
            <link rel="stylesheet" href="the_large_dict.css">
            <script type="module" src="the_large_dict.js"></script>
            {v}
            """).strip()
            f.write(f"{k}\n{content}\n</>\n")
        for k, v in redirect_data.items():
            content = (f"@@@LINK={v}").strip()
            f.write(f"{k}\n{content}\n</>\n")


if __name__ == "__main__":
    main()
