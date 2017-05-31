targethost = line.get('_uri.hostname')
targettype = None
target = None
sourcehost = line.get('referer.hostname')
sourcetype = None
source = None
v1version = None

nn = lambda value: value and re.sub(r'\d+$', r'#', value)
xx = lambda value: value and re.sub(r'(?<![a-z0-9])([0-9a-f]{2}-?)+$', r'#', value)
ah = lambda value: value and re.sub(r'^(ahreport|ahpreview).*$', r'\1#', value)
s = lambda values: '/'.join(filter(None, values)) or None
f = lambda name: line.get(name)
match = lambda pattern: functools.partial(re.search, pattern)
find = lambda values, predicate: next((i for i, value in enumerate(values) if predicate(value)), None)
first = lambda values: next((value for value in values if value != None), None)

# target parsed from 'uri'
path = list(filter(None, map(f, map(lambda n: 'uri.path.' + str(n), range(1, 9)))))
route = path[1:]
at = first(find(route, match(pattern)) for pattern in (r'\.v1$', r'\.img$'))
if at:
    route = route[at:]

if not path or not re.match(r'[a-z0-9_-]+$', path[0]):
    targettype = 'root'
elif path[0] == 's':
    targettype = 'static'
    v1version = s(path[1:2])
    target = s(path[2:3])
elif not route:
    targettype = 'other'
elif re.match(r'(rest-1|meta|query)(\.oauth|\.legacy)?\.v1', route[0]):
    targettype = 'api'
    target = route[0][:route[0].index('.')]
elif route[0] == 'ui.v1':
    targettype = 'gadget'
    target = f('uri.query.gadgettype') or f('uri.query.gadget') or 'none'
elif route[0] == 'entity.v1':
    targettype = 'entity'
    target = xx(f('uri.query.entity')) or 'none'
elif route[0] == 'export.v1':
    targettype = 'export'
    target = f('uri.query.path')
elif route[0:2] == ['gadgetview.mvc', 'rendergadget']:
    targettype = 'gadget'
    target = f('uri.query.gadgetpath')
elif route[0] == 'analyticsintegration.mvc':
    targettype = 'analytics'
    target = s(route[1:2] + [ah(f('uri.query.rdreport'))])
elif route[0] == 'report.mvc':
    targettype = 'report'
    target = s(route[1:2] + [nn(f('uri.query.report'))])
elif route[0] == 'published.mvc':
    targettype = 'mvc'
    target = xx(s(route[0:2]))
elif re.search(r'\.mvc$', route[0]):
    targettype = 'mvc'
    target = nn(s(route[0:2]))
elif route[0] == 'api' and route[1] and re.match(r'report', route[1]):
    targettype = 'report'
    target = s(route[1:3] + [nn(f('uri.query.report')) or nn(f('uri.query.reportname'))])
elif route[0] == 'api':
    targettype = 'webapi'
    target = s(route[0:2])
elif route[0] == 'default.aspx':
    page = f('uri.query.page')
    menu = f('uri.query.menu')
    targettype = (page and 'popup') or (menu and 'main') or 'home'
    target = page or menu or 'home'
else:
    targettype = 'other'
    target = route[0]

# source parsed from 'referer'
if sourcehost == targethost:
    path = list(filter(None, map(f, map(lambda n: 'referer.path.' + str(n), range(1, 9)))))
    route = path[1:]
    at = first(find(route, match(pattern)) for pattern in (r'\.v1$', r'\.img$'))
    if at:
        route = route[at:]

    if not path or not re.match(r'[a-z0-9_-]+$', path[0]):
        sourcetype = 'root'
    elif path[0] == 's':
        sourcetype = 'static'
        source = s(path[2:3])
    elif not route:
        sourcetype = 'other'
    elif re.match(r'(rest-1|meta|query)(\.oauth|\.legacy)?\.v1', route[0]):
        sourcetype = 'api'
        source = route[0][:route[0].index('.')]
    elif route[0] == 'ui.v1':
        sourcetype = 'gadget'
        source = f('referer.query.gadgettype') or f('referer.query.gadget') or 'none'
    elif route[0] == 'entity.v1':
        sourcetype = 'entity'
        source = xx(f('referer.query.entity')) or 'none'
    elif route[0] == 'export.v1':
        sourcetype = 'export'
        source = f('referer.query.path')
    elif route[0:2] == ['gadgetview.mvc', 'rendergadget']:
        sourcetype = 'gadget'
        source = f('referer.query.gadgetpath')
    elif route[0] == 'analyticsintegration.mvc':
        sourcetype = 'analytics'
        source = s(route[1:2] + [ah(f('referer.query.rdreport'))])
    elif route[0] == 'report.mvc':
        sourcetype = 'report'
        source = s(route[1:2] + [nn(f('referer.query.report'))])
    elif route[0] == 'published.mvc':
        sourcetype = 'mvc'
        source = xx(s(route[0:2]))
    elif re.search(r'\.mvc$', route[0]):
        sourcetype = 'mvc'
        source = nn(s(route[0:2]))
    elif route[0] == 'api' and route[1] and re.match(r'report', route[1]):
        sourcetype = 'report'
        source = s(route[1:3] + [nn(f('referer.query.report')) or nn(f('referer.query.reportname'))])
    elif route[0] == 'api':
        sourcetype = 'webapi'
        source = s(route[0:2])
    elif route[0] == 'default.aspx':
        page = f('referer.query.page')
        menu = f('referer.query.menu')
        sourcetype = (page and 'popup') or (menu and 'main') or 'home'
        source = page or menu or 'home'
    else:
        sourcetype = 'other'
        source = route[0]

if targettype:
    line['v1.target.type'] = targettype
if target:
    line['v1.target'] = target
if sourcetype:
    line['v1.source.type'] = sourcetype
if source:
    line['v1.source'] = source
if v1version:
    line['v1.version'] = v1version
