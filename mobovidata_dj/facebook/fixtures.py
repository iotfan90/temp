from .models import AdOptimizer, OptimizeCheck, OptimizeRule

# To start, we'll just make fixtures for the basic rules we want to test
# but this is flexible enough for more complex rules to be designed


def basic_optimizer():
    optimizer, _new = AdOptimizer.objects.get_or_create(title='Basic Optimizer',
                                                        status='manual')

    make_check = lambda a, b, c: OptimizeCheck.objects.get_or_create(if_the=a,
                                                                     check_type=b,
                                                                     value=c)[0]
    CHECK_FIXTURES = {
         'today_rule_1_spend': make_check('spend', 'gt', 20),
         'today_rule_1_conversions': make_check('sales', 'eq', 0),

         'today_rule_2_conversions': make_check('sales', 'gt', 0),
         'today_rule_2_cpa': make_check('cost_per_sale', 'gt', 12),

         'not_today_rule_1_spend': make_check('spend', 'gt', 40),
         'not_today_rule_1_conversions': make_check('sales', 'eq', 0),

         'not_today_rule_2_conversions': make_check('sales', 'gt', 0),
         'not_today_rule_2_cpa': make_check('cost_per_sale', 'gt', 20),
    }

    make_rule = lambda a, b, c: OptimizeRule.objects.get_or_create(title=a,
                                                                   applies_to=b,
                                                                   action=c)[0]
    RULE_FIXTURES = {
      'today_rule_1': make_rule('Wasted spend on a new ad', 'today', 'pause'),
      'today_rule_2': make_rule('High CPA on a new ad', 'today', 'pause'),
      'not_today_rule_1': make_rule('Wasted spend on an existing ad',
                                    'not_today', 'pause'),
      'not_today_rule_2': make_rule('High CPA on an existing ad', 'not_today',
                                    'pause'),
    }

    if _new:
        RULE_FIXTURES['today_rule_1'].checks.add(CHECK_FIXTURES['today_rule_1_spend'])
        RULE_FIXTURES['today_rule_1'].checks.add(CHECK_FIXTURES['today_rule_1_conversions'])

        RULE_FIXTURES['today_rule_2'].checks.add(CHECK_FIXTURES['today_rule_2_conversions'])
        RULE_FIXTURES['today_rule_2'].checks.add(CHECK_FIXTURES['today_rule_2_cpa'])

        RULE_FIXTURES['not_today_rule_1'].checks.add(CHECK_FIXTURES['not_today_rule_1_spend'])
        RULE_FIXTURES['not_today_rule_1'].checks.add(CHECK_FIXTURES['not_today_rule_1_conversions'])

        RULE_FIXTURES['not_today_rule_2'].checks.add(CHECK_FIXTURES['not_today_rule_2_conversions'])
        RULE_FIXTURES['not_today_rule_2'].checks.add(CHECK_FIXTURES['not_today_rule_2_cpa'])

        optimizer.rules.set(RULE_FIXTURES.values())
    return optimizer
