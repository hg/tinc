#!/usr/bin/env python3

import os
import sys
from pathlib import Path

from testlib import Tinc, log, check

node = Tinc()
stdout, _ = node.cmd('--version')
with_legacy = 'legacy_protocol' in stdout


class Context:
    def __init__(self):
        node = Tinc()
        node.cmd('init', node.name)

        self.n = node
        self.dir = node.wd
        self.host = node.sub('hosts', node.name)
        self.conf = node.sub('tinc.conf')
        self.rsa_priv = node.sub('rsa_key.priv')
        self.ec_priv = node.sub('ed25519_key.priv')
        self.tinc_up = node.sub('tinc-up')
        self.host_up = node.sub('host-up')

        if os.name == 'nt':
            self.tinc_up = f'{self.tinc_up}.cmd'
            self.host_up = f'{self.host_up}.cmd'

    def expect_msg(self, msg: str, force: bool = False, code: int = 1, present: bool = True) -> None:
        args = ['fsck']
        if force:
            args.insert(0, '--force')

        out, err = self.n.cmd(*args, code=code)
        if present:
            check.in_(msg, out, err)
        else:
            check.not_in(msg, out, err)


def test(msg: str) -> Context:
    global ctx
    ctx = Context()
    log.info('TEST: %s', msg)
    return ctx


def read_text(path: str) -> str:
    with open(path) as f:
        return f.read()


def read_lines(path: str) -> [str]:
    return read_text(path).splitlines()


def write_lines(path: str, lines: [str]) -> None:
    Path(path).write_text('\n'.join(lines) + '\n')


def remove_pem(path: str) -> [str]:
    lines = read_lines(path)
    key, result = False, []
    for line in lines:
        if line.startswith('-----BEGIN'):
            key = True
            continue
        if line.startswith('-----END'):
            key = False
            continue
        if not key:
            result.append(line)
    write_lines(path, result)
    return result


def extract_pem(path: str) -> [str]:
    lines = read_lines(path)
    key, result = False, []
    for line in lines:
        if line.startswith('-----BEGIN'):
            key = True
            continue
        if line.startswith('-----END'):
            return result
        if key:
            result.append(line)
    raise Exception('key not found')


def replace_line(path: str, prefix: str, replace: str = ''):
    lines = read_lines(path)
    lines = [replace if line.startswith(prefix) else line for line in lines]
    write_lines(path, lines)


run_access_checks = os.name != 'nt' and os.geteuid() == 0

# Sample RSA key pair (old format). Uses e = 0xFFFF.
rsa_n = '''
BB82C3A9B906E98ABF2D99FF9B320B229F5C1E58EC784762DA1F4D3509FFF78ECA7FFF19BA17073\
6CDE458EC8E732DDE2C02009632DF731B4A6BD6C504E50B7B875484506AC1E49FD0DF624F6612F5\
64C562BD20F870592A49195023D744963229C35081C8AE48BE2EBB5CC9A0D64924022DC0EB782A3\
A8F3EABCA04AA42B24B2A6BD2353A6893A73AE01FA54891DD24BF36CA032F19F7E78C01273334BA\
A2ECF36B6998754CB012BC985C975503D945E4D925F6F719ACC8FBA7B18C810FF850C3CCACD6056\
5D4FCFE02A98FE793E2D45D481A34D1F90584D096561FF3184C462C606535F3F9BB260541DF0D1F\
EB16938FFDEC2FF96ACCC6BD5BFBC19471F6AB
'''.strip()

rsa_d = '''
8CEC9A4316FE45E07900197D8FBB52D3AF01A51C4F8BD08A1E21A662E3CFCF7792AD7680673817B\
70AC1888A08B49E8C5835357016D9BF56A0EBDE8B5DF214EC422809BC8D88177F273419116EF2EC\
7951453F129768DE9BC31D963515CC7481559E4C0E65C549169F2B94AE68DB944171189DD654DC6\
970F2F5843FB7C8E9D057E2B5716752F1F5686811AC075ED3D3CBD06B5D35AE33D01260D9E0560A\
F545D0C9D89A31D5EAF96D5422F6567FE8A90E23906B840545805644DFD656E526A686D3B978DD2\
71578CA3DA0F7D23FC1252A702A5D597CAE9D4A5BBF6398A75AF72582C7538A7937FB71A2610DCB\
C39625B77103FA3B7D0A55177FD98C39CD4A27
'''.strip()

ctx = test('newly created configuration should pass')
ctx.n.cmd('fsck')

ctx = test('fail on missing tinc.conf')
os.remove(ctx.conf)
ctx.expect_msg('No tinc configuration found')

if run_access_checks:
    ctx = test('fail on inaccessible tinc.conf')
    os.chmod(ctx.dir, 000)
    ctx.expect_msg('not running tinc as root')

if os.name != 'nt':
    ctx = test('non-executable tinc-up MUST be fixed by tinc --force')
    os.chmod(ctx.tinc_up, 0o644)
    ctx.expect_msg('cannot read and execute', force=True, code=0)
    assert os.access(ctx.tinc_up, os.X_OK)

    ctx = test('non-executable tinc-up MUST NOT be fixed by tinc without --force')
    os.chmod(ctx.tinc_up, 0o644)
    ctx.expect_msg('cannot read and execute', code=0)
    assert not os.access(ctx.tinc_up, os.X_OK)

for suffix in ('up', 'down'):
    ctx = test(f'unknown -{suffix} script warning')
    with open(ctx.n.sub(f'fake-{suffix}'), 'w') as f:
        f.write('')
    ctx.expect_msg('Unknown script', code=0)

if os.name != 'nt':
    ctx = test('non-executable foo-up MUST be fixed by tinc --force')
    with open(ctx.host_up, 'w') as f:
        f.write('')
    os.chmod(ctx.host_up, 0o644)
    ctx.expect_msg('cannot read and execute', force=True, code=0)
    assert os.access(ctx.tinc_up, os.X_OK)

    ctx = test('non-executable bar-up MUST NOT be fixed by tinc')
    path = ctx.n.sub('hosts', 'bar-up')
    with open(path, 'w') as f:
        f.write('')
    os.chmod(path, 0o644)
    ctx.expect_msg('cannot read and execute', code=0)
    assert not os.access(path, os.X_OK)

if run_access_checks:
    ctx = test('inaccessible hosts/foo must fail')
    os.chmod(ctx.host, 0)
    ctx.expect_msg('Cannot open config file')

ctx = test('fix broken Ed25519 public key with --force')
replace_line(ctx.host, 'Ed25519PublicKey', 'Ed25519PublicKey = foobar')
ctx.expect_msg('No (usable) public Ed25519 key', force=True, code=0)
ctx.n.cmd('fsck')

ctx = test('fix missing Ed25519 public key with --force')
replace_line(ctx.host, 'Ed25519PublicKey')
ctx.expect_msg('No (usable) public Ed25519 key', force=True, code=0)
ctx.n.cmd('fsck')

ctx = test('fail when all private keys are missing')
os.remove(ctx.ec_priv)
if with_legacy:
    os.remove(ctx.rsa_priv)
    ctx.expect_msg('Neither RSA or Ed25519 private')
else:
    ctx.expect_msg('No Ed25519 private')

ctx = test('warn about missing EC public key and NOT fix without --force')
replace_line(ctx.host, 'Ed25519PublicKey')
ctx.expect_msg('No (usable) public Ed25519', code=0)
with open(ctx.host, 'r') as f:
    host = f.read()
check.not_in('ED25519 PUBLIC KEY', host)

ctx = test('fix missing EC public key on --force')
replace_line(ctx.host, 'Ed25519PublicKey')
ctx.expect_msg('Wrote Ed25519 public key', force=True, code=0)
with open(ctx.host, 'r') as f:
    host = f.read()
check.in_('ED25519 PUBLIC KEY', host)

ctx = test('warn about obsolete variables')
with open(ctx.host, 'a') as f:
    f.write('\nGraphDumpFile = /dev/null\n')
ctx.expect_msg('obsolete variable GraphDumpFile', code=0)

ctx = test('warn about missing values')
with open(ctx.host, 'a') as f:
    f.write('\nWeight = \n')
ctx.expect_msg('No value for variable `Weight')

ctx = test('warn about duplicate variables')
with open(ctx.host, 'a') as f:
    f.write('\nWeight = 0\nWeight = 1')
ctx.expect_msg('multiple instances of variable Weight', code=0)

ctx = test('warn about server variables in host config')
with open(ctx.host, 'a') as f:
    f.write('\nInterface = fake0\n')
ctx.expect_msg('server variable Interface found', code=0)

ctx = test('warn about host variables in server config')
with open(ctx.conf, 'a') as f:
    f.write('\nPort = 1337\n')
ctx.expect_msg('host variable Port found', code=0)

ctx = test('warn about missing Name')
replace_line(ctx.conf, 'Name =')
ctx.expect_msg('without a valid Name')


def test_private_key_var(var: str, file: str):
    ctx = test(f'private key variable {var} in file {file}')
    renamed = os.path.realpath(ctx.n.sub('renamed_key'))
    os.rename(src=ctx.n.sub(file), dst=renamed)
    with open(ctx.conf, 'a') as f:
        f.write(f'\n{var} = {renamed}\n')
    ctx.expect_msg('key was found but no private key', present=False, code=0)


def test_private_keys(keyfile: str):
    ctx = test(f'fail on broken {keyfile}')
    path = ctx.n.sub(keyfile)
    os.truncate(path, 0)
    if with_legacy:
        ctx.expect_msg('no private key is known', code=0)
    else:
        ctx.expect_msg('No Ed25519 private key found')

    if run_access_checks:
        ctx = test(f'fail on inaccessible {keyfile}')
        path = ctx.n.sub(keyfile)
        os.chmod(path, 0)
        ctx.expect_msg('error reading', code=0 if with_legacy else 1)

    if os.name != 'nt':
        ctx = test(f'warn about unsafe permissions on {keyfile}')
        path = ctx.n.sub(keyfile)
        os.chmod(path, 0o666)
        ctx.expect_msg('unsafe file permissions', code=0)

    if with_legacy:
        ctx = test(f'pass on missing {keyfile} when the other key is present')
        path = ctx.n.sub(keyfile)
        os.remove(path)
        ctx.n.cmd('fsck')


def test_ec_public_key_file_var(ctx: Context, *paths: str):
    ec_pubkey = os.path.realpath(ctx.n.sub('ec_pubkey'))

    ec_key = ''
    with open(ctx.host, 'r') as f:
        for line in f:
            if line.startswith('Ed25519PublicKey'):
                _, _, ec_key = line.split()
                break
    assert ec_key

    with open(ec_pubkey, 'w') as f:
        f.write(f'''
-----BEGIN ED25519 PUBLIC KEY-----
{ec_key}
-----END ED25519 PUBLIC KEY-----
        ''')

    replace_line(ctx.host, 'Ed25519PublicKey')

    path = ctx.n.sub(*paths)
    with open(path, 'a') as f:
        f.write(f'\nEd25519PublicKeyFile = {ec_pubkey}\n')

    ctx.expect_msg('No (usable) public Ed25519', code=0, present=False)


test_private_keys('ed25519_key.priv')
test_private_key_var('Ed25519PrivateKeyFile', 'ed25519_key.priv')

ctx = test('test EC public key in tinc.conf')
test_ec_public_key_file_var(ctx, 'tinc.conf')

ctx = test('test EC public key in hosts/')
test_ec_public_key_file_var(ctx, 'hosts', ctx.n.name)

###############################################################################
# legacy protocol
###############################################################################
if not with_legacy:
    log.info('skipping legacy protocol tests')
    sys.exit(0)


def test_rsa_public_key_file_var(ctx: Context, *paths: str):
    key = extract_pem(ctx.host)
    remove_pem(ctx.host)

    rsa_pub = os.path.realpath(ctx.n.sub('rsa_pubkey'))
    write_lines(rsa_pub, key)

    path = ctx.n.sub(*paths)
    with open(path, 'a') as f:
        f.write(f'\nPublicKeyFile = {rsa_pub}\n')

    ctx.expect_msg('Error reading RSA public key', code=0, present=False)


test_private_keys('rsa_key.priv')
test_private_key_var('PrivateKeyFile', 'rsa_key.priv')

ctx = test('test rsa public key in tinc.conf')
test_rsa_public_key_file_var(ctx, 'tinc.conf')

ctx = test('test rsa public key in hosts/')
test_rsa_public_key_file_var(ctx, 'hosts', ctx.n.name)

if os.name != 'nt':
    ctx = test('warn about unsafe permissions on tinc.conf with PrivateKey')
    os.remove(ctx.rsa_priv)
    with open(ctx.conf, 'a') as f:
        f.write(f'\nPrivateKey = {rsa_d}\n')
    with open(ctx.host, 'a') as f:
        f.write(f'\nPublicKey = {rsa_n}\n')
    os.chmod(ctx.conf, 0o666)
    ctx.expect_msg('unsafe file permissions', code=0)

ctx = test('warn about missing RSA private key if public key is present')
os.remove(ctx.rsa_priv)
ctx.expect_msg('public RSA key was found but no private key', code=0)

ctx = test('warn about missing RSA public key')
remove_pem(ctx.host)
ctx.expect_msg('No (usable) public RSA', code=0)
check.not_in('BEGIN RSA PUBLIC KEY', read_text(ctx.host))

ctx = test('fix missing RSA public key on --force')
remove_pem(ctx.host)
ctx.expect_msg('Wrote RSA public key', force=True, code=0)
check.in_('BEGIN RSA PUBLIC KEY', read_text(ctx.host))

ctx = test('RSA PublicKey + PrivateKey must work')
os.remove(ctx.rsa_priv)
remove_pem(ctx.host)
with open(ctx.conf, 'a') as f:
    f.write(f'\nPrivateKey = {rsa_d}\n')
with open(ctx.host, 'a') as f:
    f.write(f'\nPublicKey = {rsa_n}\n')
ctx.expect_msg('no (usable) public RSA', code=0, present=False)

ctx = test('RSA PrivateKey without PublicKey must warn')
os.remove(ctx.rsa_priv)
remove_pem(ctx.host)
with open(ctx.conf, 'a') as f:
    f.write(f'\nPrivateKey = {rsa_d}\n')
ctx.expect_msg('PrivateKey used but no PublicKey found', code=0)

ctx = test('warn about missing EC private key if public key is present')
os.remove(ctx.ec_priv)
ctx.expect_msg('public Ed25519 key was found but no private key', code=0)

ctx = test('fix broken RSA public key with --force')
lines = read_lines(ctx.host)
del lines[1]
write_lines(ctx.host, lines)
ctx.expect_msg('old key(s) found and disabled', force=True, code=0)
ctx.n.cmd('fsck')

ctx = test('fix missing RSA public key with --force')
remove_pem(ctx.host)
ctx.expect_msg('No (usable) public RSA key found', force=True, code=0)
ctx.n.cmd('fsck')
