from collections import defaultdict
from facebookads.adobjects import campaign, adset

from mobovidata_dj.facebook.connect import FacebookConnect


def get_facebook_campaign_and_ads_info(fb_credentials=None):
    """
    Get the necessary information from FacebookConnect such as campaigns and
    ad_sets
    :return: tuple
    """
    p = FacebookConnect(**fb_credentials)
    rg_campaigns = p.get_campaigns()
    rg_ad_sets = p.get_ad_sets()
    ms_campaign_ids = set()
    mp_ad_sets = defaultdict(list)
    for x in rg_ad_sets:
        st_campaign_id = x[adset.AdSet.Field.campaign_id]
        ms_campaign_ids.add(st_campaign_id)
        mp_ad_sets[st_campaign_id].append({
            'name': x[adset.AdSet.Field.name],
            'ad_set_id': x[adset.AdSet.Field.id],
        })
    rg_temp = []
    for x in rg_campaigns:
        st_campaign_id = x[campaign.Campaign.Field.id]
        if st_campaign_id in ms_campaign_ids:
            rg_temp.append({
                'name': x[campaign.Campaign.Field.name],
                'campaign_id': st_campaign_id
            })
    rg_temp = sorted(rg_temp, key=lambda k: k['name'])
    return rg_temp, mp_ad_sets
