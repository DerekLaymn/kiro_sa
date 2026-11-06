"""Day 8 phase 5: yield of the retirement candidates. For each parent name, over the Day-8 judge run (runs/day8/out) and
the Day-7 judge run replayed with the final KB (runs/day8/day7replay-it2): programs, live findings, dismissed findings by
entry, tool crashes. A parent whose mutants have 0 live findings only rediscovers known issues."""
import collections, glob, json, os

R = '/home/derek/Projects/5th_sem/Software_analysis/project/kiro_sa/'
PARENTS = ['d3p_paramspec_identity_applied_to_itself', 'd3p_paramspec_self_annotated_dunder_call',
           'd4v_eq_no_hash_hashable', 'd4p_inheritance_hash_none_from_eq', 'd3p_inheritance_mro_hash_none_from_eq',
           'd3p_generics_callable_attr_contravariant', 'd3p_descriptors_decorated_get',
           'd4p_descriptors_readonly_prop_never', 'd5p_descriptors_decorated_get_pyright_rangeerror',
           'd5p_descriptors_one_decorator_dunders_pyright_rangeerror', 'd7p_tuples_unpacking_partial_unpack_except_ty']
for label, out in (('day8 judge run', R + 'runs/day8/out'), ('day7 judge run, final KB', R + 'runs/day8/day7replay-it2')):
    print('==', label, out)
    stat = {p: collections.Counter() for p in PARENTS}
    ent = {p: collections.Counter() for p in PARENTS}
    for f in sorted(glob.glob(out + '/seed-*.json')):
        d = json.load(open(f))
        org = [x for x in d['notes'] if x.startswith('origin=')]
        base = os.path.basename((org[0][7:] if org else '').replace('seed ', ''))
        parent = base.split('__mut')[0]
        if parent not in stat:
            continue
        live = [fi for fi in d['findings'] if fi['dismissal'] is None]
        dis = [fi for fi in d['findings'] if fi['dismissal'] is not None]
        c = stat[parent]
        c['programs'] += 1
        c['live'] += len(live)
        c['dismissed'] += len(dis)
        c['tool_crashes'] += len(d.get('crashes') or [])
        for fi in dis:
            ent[parent][str(fi['dismissal'])[:60]] += 1
    for p in PARENTS:
        print('  %-58s %s %s' % (p, dict(stat[p]), dict(ent[p])))
