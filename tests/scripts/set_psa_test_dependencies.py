#!/usr/bin/env python3

"""Edit test cases to use PSA dependencies instead of classic dependencies.
"""

# Copyright The Mbed TLS Contributors
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import sys

CLASSIC_DEPENDENCIES = frozenset([
    # This list is manually filtered from config.h.

    # Mbed TLS feature support.
    # Only features that affect what can be done are listed here.
    # Options that control optimizations or alternative implementations
    # are omitted.
    #cipher#'MBEDTLS_CIPHER_MODE_CBC',
    #cipher#'MBEDTLS_CIPHER_MODE_CFB',
    #cipher#'MBEDTLS_CIPHER_MODE_CTR',
    #cipher#'MBEDTLS_CIPHER_MODE_OFB',
    #cipher#'MBEDTLS_CIPHER_MODE_XTS',
    #cipher#'MBEDTLS_CIPHER_NULL_CIPHER',
    #cipher#'MBEDTLS_CIPHER_PADDING_PKCS7',
    #cipher#'MBEDTLS_CIPHER_PADDING_ONE_AND_ZEROS',
    #cipher#'MBEDTLS_CIPHER_PADDING_ZEROS_AND_LEN',
    #cipher#'MBEDTLS_CIPHER_PADDING_ZEROS',
    #curve#'MBEDTLS_ECP_DP_SECP192R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_SECP224R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_SECP256R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_SECP384R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_SECP521R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_SECP192K1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_SECP224K1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_SECP256K1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_BP256R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_BP384R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_BP512R1_ENABLED',
    #curve#'MBEDTLS_ECP_DP_CURVE25519_ENABLED',
    #curve#'MBEDTLS_ECP_DP_CURVE448_ENABLED',
    'MBEDTLS_ECDSA_DETERMINISTIC',
    #'MBEDTLS_GENPRIME', #needed for RSA key generation
    'MBEDTLS_PKCS1_V15',
    'MBEDTLS_PKCS1_V21',
    'MBEDTLS_SHA512_NO_SHA384',

    # Mbed TLS modules.
    # Only modules that provide cryptographic mechanisms are listed here.
    # Platform, data formatting, X.509 or TLS modules are omitted.
    #cipher#'MBEDTLS_AES_C',
    #cipher#'MBEDTLS_ARC4_C',
    'MBEDTLS_BIGNUM_C',
    #cipher#'MBEDTLS_BLOWFISH_C',
    #cipher#'MBEDTLS_CAMELLIA_C',
    #cipher#'MBEDTLS_ARIA_C',
    #cipher#'MBEDTLS_CCM_C',
    #cipher#'MBEDTLS_CHACHA20_C',
    #cipher#'MBEDTLS_CHACHAPOLY_C',
    #cipher#'MBEDTLS_CMAC_C',
    'MBEDTLS_CTR_DRBG_C',
    #cipher#'MBEDTLS_DES_C',
    'MBEDTLS_DHM_C',
    'MBEDTLS_ECDH_C',
    'MBEDTLS_ECDSA_C',
    'MBEDTLS_ECJPAKE_C',
    'MBEDTLS_ECP_C',
    'MBEDTLS_ENTROPY_C',
    #cipher#'MBEDTLS_GCM_C',
    'MBEDTLS_HKDF_C',
    'MBEDTLS_HMAC_DRBG_C',
    #cipher#'MBEDTLS_NIST_KW_C',
    'MBEDTLS_MD2_C',
    'MBEDTLS_MD4_C',
    'MBEDTLS_MD5_C',
    'MBEDTLS_PKCS5_C',
    'MBEDTLS_PKCS12_C',
    #cipher#'MBEDTLS_POLY1305_C',
    #cipher#'MBEDTLS_RIPEMD160_C',
    'MBEDTLS_RSA_C',
    'MBEDTLS_SHA1_C',
    'MBEDTLS_SHA256_C',
    'MBEDTLS_SHA512_C',
    'MBEDTLS_XTEA_C',
])

def is_classic_dependency(dep):
    """Whether dep is a classic dependency that PSA test cases should not use."""
    if dep.startswith('!'):
        dep = dep[1:]
    return dep in CLASSIC_DEPENDENCIES

def is_systematic_dependency(dep):
    """Whether dep is a PSA dependency which is determined systematically."""
    return dep.startswith('PSA_WANT_')

WITHOUT_SYSTEMATIC_DEPENDENCIES = frozenset([
    'PSA_ALG_AEAD_WITH_TAG_LENGTH', # only a modifier
    'PSA_ALG_ANY_HASH', # only meaningful in policies
    'PSA_ALG_KEY_AGREEMENT', # only a way to combine algorithms
    'PSA_ALG_TRUNCATED_MAC', # only a modifier
    'PSA_KEY_TYPE_NONE', # always supported
    'PSA_KEY_TYPE_DERIVE', # always supported
    'PSA_KEY_TYPE_RAW_DATA', # always supported

    # Not implemented yet: cipher-related key types and algorithms.
    # Manually extracted from crypto_values.h.
    'PSA_KEY_TYPE_AES',
    'PSA_KEY_TYPE_DES',
    'PSA_KEY_TYPE_CAMELLIA',
    'PSA_KEY_TYPE_ARC4',
    'PSA_KEY_TYPE_CHACHA20',
    'PSA_ALG_CBC_MAC',
    'PSA_ALG_CMAC',
    'PSA_ALG_STREAM_CIPHER',
    'PSA_ALG_CTR',
    'PSA_ALG_CFB',
    'PSA_ALG_OFB',
    'PSA_ALG_XTS',
    'PSA_ALG_ECB_NO_PADDING',
    'PSA_ALG_CBC_NO_PADDING',
    'PSA_ALG_CBC_PKCS7',
    'PSA_ALG_CCM',
    'PSA_ALG_GCM',
    'PSA_ALG_CHACHA20_POLY1305',
])

SPECIAL_SYSTEMATIC_DEPENDENCIES = {
    'PSA_ALG_ECDSA_ANY': frozenset(['PSA_WANT_ALG_ECDSA']),
    'PSA_ALG_RSA_PKCS1V15_SIGN_RAW': frozenset(['PSA_WANT_ALG_RSA_PKCS1V15_SIGN']),
}

def dependencies_of_symbol(symbol):
    """Return the dependencies for a symbol that designates a cryptographic mechanism."""
    if symbol in WITHOUT_SYSTEMATIC_DEPENDENCIES:
        return frozenset()
    if symbol in SPECIAL_SYSTEMATIC_DEPENDENCIES:
        return SPECIAL_SYSTEMATIC_DEPENDENCIES[symbol]
    if symbol.startswith('PSA_ALG_CATEGORY_') or \
       symbol.startswith('PSA_KEY_TYPE_CATEGORY_'):
        # Categories are used in test data when an unsupported but plausible
        # mechanism number needed. They have no associated dependency.
        return frozenset()
    return {symbol.replace('_', '_WANT_', 1)}

def systematic_dependencies(file_name, function_name, arguments):
    #pylint: disable=unused-argument
    """List the systematically determined dependency for a test case."""
    deps = set()

    # Run key policy negative tests even if the algorithm to attempt performing
    # is not supported.
    if function_name.endswith('_key_policy') and \
       arguments[-1].startswith('PSA_ERROR_'):
        arguments[-2] = ''

    for arg in arguments:
        for symbol in re.findall(r'PSA_(?:ALG|KEY_TYPE)_\w+', arg):
            deps.update(dependencies_of_symbol(symbol))
    return sorted(deps)

def updated_dependencies(file_name, function_name, arguments, dependencies):
    """Rework the list of dependencies into PSA_WANT_xxx.

    Remove classic crypto dependencies such as MBEDTLS_RSA_C,
    MBEDTLS_PKCS1_V15, etc.

    Add systematic PSA_WANT_xxx dependencies based on the called function and
    its arguments, replacing existing PSA_WANT_xxx dependencies.
    """
    automatic = systematic_dependencies(file_name, function_name, arguments)
    manual = [dep for dep in dependencies
              if not (is_systematic_dependency(dep) or
                      is_classic_dependency(dep))]
    return automatic + manual

def keep_manual_dependencies(file_name, function_name, arguments):
    #pylint: disable=unused-argument
    """Declare test functions with unusual dependencies here."""
    # If there are no arguments, we can't do any useful work. Assume that if
    # there are dependencies, they are warranted.
    if not arguments:
        return True
    # When PSA_ERROR_NOT_SUPPORTED is expected, usually, at least one of the
    # constants mentioned in the test should not be supported. It isn't
    # possible to determine which one in a systematic way. So let the programmer
    # decide.
    if arguments[-1] == 'PSA_ERROR_NOT_SUPPORTED':
        return True
    return False

def process_data_stanza(stanza, file_name, test_case_number):
    """Update PSA crypto dependencies in one Mbed TLS test case.

    stanza is the test case text (including the description, the dependencies,
    the line with the function and arguments, and optionally comments). Return
    a new stanza with an updated dependency line, preserving everything else
    (description, comments, arguments, etc.).
    """
    if not stanza.lstrip('\n'):
        # Just blank lines
        return stanza
    # Expect 2 or 3 non-comment lines: description, optional dependencies,
    # function-and-arguments.
    content_matches = list(re.finditer(r'^[\t ]*([^\t #].*)$', stanza, re.M))
    if len(content_matches) < 2:
        raise Exception('Not enough content lines in paragraph {} in {}'
                        .format(test_case_number, file_name))
    if len(content_matches) > 3:
        raise Exception('Too many content lines in paragraph {} in {}'
                        .format(test_case_number, file_name))
    arguments = content_matches[-1].group(0).split(':')
    function_name = arguments.pop(0)
    if keep_manual_dependencies(file_name, function_name, arguments):
        return stanza
    if len(content_matches) == 2:
        # Insert a line for the dependencies. If it turns out that there are
        # no dependencies, we'll remove that empty line below.
        dependencies_location = content_matches[-1].start()
        text_before = stanza[:dependencies_location]
        text_after = '\n' + stanza[dependencies_location:]
        old_dependencies = []
        dependencies_leader = 'depends_on:'
    else:
        dependencies_match = content_matches[-2]
        text_before = stanza[:dependencies_match.start()]
        text_after = stanza[dependencies_match.end():]
        old_dependencies = dependencies_match.group(0).split(':')
        dependencies_leader = old_dependencies.pop(0) + ':'
        if dependencies_leader != 'depends_on:':
            raise Exception('Next-to-last line does not start with "depends_on:"'
                            ' in paragraph {} in {}'
                            .format(test_case_number, file_name))
    new_dependencies = updated_dependencies(file_name, function_name, arguments,
                                            old_dependencies)
    if new_dependencies:
        stanza = (text_before +
                  dependencies_leader + ':'.join(new_dependencies) +
                  text_after)
    else:
        # The dependencies have become empty. Remove the depends_on: line.
        assert text_after[0] == '\n'
        stanza = text_before + text_after[1:]
    return stanza

def process_data_file(file_name, old_content):
    """Update PSA crypto dependencies in an Mbed TLS test suite data file.

    Process old_content (the old content of the file) and return the new content.
    """
    old_stanzas = old_content.split('\n\n')
    new_stanzas = [process_data_stanza(stanza, file_name, n)
                   for n, stanza in enumerate(old_stanzas, start=1)]
    return '\n\n'.join(new_stanzas)

def update_file(file_name, old_content, new_content):
    """Update the given file with the given new content.

    Replace the existing file. The previous version is renamed to *.bak.
    Don't modify the file if the content was unchanged.
    """
    if new_content == old_content:
        return
    backup = file_name + '.bak'
    tmp = file_name + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as new_file:
        new_file.write(new_content)
    os.replace(file_name, backup)
    os.replace(tmp, file_name)

def process_file(file_name):
    """Update PSA crypto dependencies in an Mbed TLS test suite data file.

    Replace the existing file. The previous version is renamed to *.bak.
    Don't modify the file if the content was unchanged.
    """
    old_content = open(file_name, encoding='utf-8').read()
    if file_name.endswith('.data'):
        new_content = process_data_file(file_name, old_content)
    else:
        raise Exception('File type not recognized: {}'
                        .format(file_name))
    update_file(file_name, old_content, new_content)

def main(args):
    for file_name in args:
        process_file(file_name)

if __name__ == '__main__':
    main(sys.argv[1:])
