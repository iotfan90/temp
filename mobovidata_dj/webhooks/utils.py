def get_data_as_formset(data, prefix='form', total_forms=u'1',
                        initial_forms=u'0', max_num_forms=u''):
    """
    Quick function for making formset data out of dicts and lists of dicts.
    :param list or dict data: data to load in the formset
    :param str prefix: prefix label for formset
    :param str total_forms:
    :param str initial_forms:
    :param str max_num_forms:
    :return dict: formset data
    """
    r = {
        '%s-TOTAL_FORMS' % prefix: total_forms,
        '%s-INITIAL_FORMS' % prefix: initial_forms,
        '%s-MAX_NUM_FORMS' % prefix: max_num_forms,
    }

    if type(data) is dict:
        data = [data, ]
    for idx, a in zip(range(len(data)), data):
        for k, v in a.items():
            r['%s-%s-%s' % (prefix, idx, k.lower())] = v
    return r
