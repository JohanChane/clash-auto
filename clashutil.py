from ruamel.yaml.comments import CommentedMap
from ruamel.yaml.comments import CommentedSeq

def merge_dict(a, b):
    if isinstance(a, CommentedMap) and isinstance(b, CommentedMap):
        for k, v in b.items():
            if k in a:
                a[k] = merge_dict(a[k], v)
            else:
                a[k] = v
        return a
    elif isinstance(a, CommentedSeq) and isinstance(b, CommentedSeq):
        for i, v in enumerate(b):
            if i < len(a):
                a[i] = merge_dict(a[i], v)
            else:
                a.append(v)
        return a
    else:
        return b