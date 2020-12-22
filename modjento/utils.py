import copy


def chunk_ids(rg_ids, n_size=1000):
    rg_chunks = []
    rg = copy.copy(rg_ids)
    while rg:
        rg_chunks.append(rg[:n_size])
        rg = rg[n_size:]
    return rg_chunks


def save_percent(retail_price, special_price, item_id=None):
    if not retail_price:
        if special_price:
            retail_price = special_price
        else:
            return None
    if not special_price:
        if retail_price:
            special_price = retail_price
        else:
            return None
    save_percent = round(((float(retail_price) - float(special_price)) / float(retail_price)) * 100, 2)
    return save_percent
