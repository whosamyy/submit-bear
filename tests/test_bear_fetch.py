"""Run: .venv/bin/python -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from bear_fetch.server import inspect_repo

ROOT = Path(__file__).resolve().parents[1]
SHA = 'a' * 40
TREE = 'b' * 40
URL = 'https://github.com/example/project'


class RepoTests(unittest.IsolatedAsyncioTestCase):
    async def check(self, *, url=URL, paths=None, ref=None, failure=None,
                    truncated=False, private=False, malformed=False):
        requests = []

        def handler(request):
            requests.append(request)
            self.assertEqual(request.method, 'GET')
            self.assertEqual(request.url.host, 'api.github.com')
            self.assertNotIn('authorization', request.headers)
            path = request.url.path
            if failure and failure[0] in path:
                if failure[1] == 'network':
                    raise httpx.ConnectError('offline', request=request)
                return httpx.Response(failure[1], headers={'x-ratelimit-remaining': '0'})
            if path.endswith('/project'):
                return httpx.Response(200, json={'private': private, 'default_branch': 'main'})
            if '/commits/' in path:
                return httpx.Response(200, json={'sha': SHA, 'commit': {'tree': {'sha': TREE}}})
            self.assertTrue(path.endswith('/git/trees/' + TREE))
            self.assertEqual(request.url.params['recursive'], '1')
            if malformed:
                return httpx.Response(200, text='not JSON')
            return httpx.Response(200, json={'truncated': truncated, 'tree': [
                {'path': 'README.md', 'type': 'blob', 'mode': '100644'},
                {'path': 'docs', 'type': 'tree', 'mode': '040000'},
                {'path': 'link', 'type': 'blob', 'mode': '120000'},
            ]})

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            result = await inspect_repo(url, paths or ['README.md', 'absent.txt'], ref, client)
        return result, requests

    async def test_default_branch_and_pinned_snapshot(self):
        result, requests = await self.check()
        self.assertEqual(result['ref'], 'main')
        self.assertEqual(result['remote_commit_sha'], SHA)
        self.assertEqual(result['found'], ['README.md'])
        self.assertEqual(result['missing'], ['absent.txt'])
        self.assertEqual(result['errors'], [])
        self.assertEqual(len(requests), 3)

    async def test_explicit_ref(self):
        result, requests = await self.check(ref='feature/test')
        self.assertEqual(result['ref'], 'feature/test')
        self.assertIn('feature%2Ftest', str(requests[1].url))

    async def test_invalid_urls_make_no_requests(self):
        for url in ['https://evil.test/a/b', 'http://github.com/a/b',
                    'https://github.com@evil.test/a/b', 'https://github.com/a/b/tree/main',
                    'https://github.com/a/b?token=secret', 'https://github.com:443/a/b']:
            result, requests = await self.check(url=url)
            self.assertTrue(result['errors'])
            self.assertEqual(requests, [])
            self.assertEqual(result['missing'], [])

    async def test_invalid_paths_make_no_requests(self):
        for path in ['../README.md', '/README.md', 'a//b', 'a/./b']:
            result, requests = await self.check(paths=[path])
            self.assertTrue(result['errors'])
            self.assertEqual(requests, [])

    async def test_api_failures_never_mean_missing(self):
        for endpoint, status in [('/project', 404), ('/commits/', 404),
                                 ('/git/trees/', 404), ('/git/trees/', 403),
                                 ('/git/trees/', 429), ('/git/trees/', 500),
                                 ('/project', 'network')]:
            result, _ = await self.check(failure=(endpoint, status))
            self.assertTrue(result['errors'])
            self.assertEqual(result['missing'], [])
            self.assertEqual(result['unverified'], ['README.md', 'absent.txt'])

    async def test_private_repository_rejected(self):
        result, requests = await self.check(private=True)
        self.assertTrue(result['errors'])
        self.assertEqual(len(requests), 1)

    async def test_truncated_tree_does_not_prove_absence(self):
        result, _ = await self.check(truncated=True)
        self.assertEqual(result['found'], ['README.md'])
        self.assertEqual(result['missing'], [])
        self.assertEqual(result['unverified'], ['absent.txt'])

    async def test_nonfiles_are_unverified(self):
        result, _ = await self.check(paths=['docs', 'link'])
        self.assertEqual(result['unverified'], ['docs', 'link'])
        self.assertEqual(result['found'], [])

    async def test_malformed_response(self):
        result, _ = await self.check(malformed=True)
        self.assertTrue(result['errors'])
        self.assertEqual(result['missing'], [])


class ProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_initialize_discover_and_call(self):
        params = StdioServerParameters(command=sys.executable,
                                        args=[str(ROOT / 'bear_fetch/server.py')])
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                initialized = await session.initialize()
                self.assertEqual(initialized.serverInfo.name, 'Bear Fetch')
                listing = await session.list_tools()
                self.assertEqual([t.name for t in listing.tools], ['check_public_repo'])
                tool = listing.tools[0]
                self.assertEqual(tool.inputSchema['required'], ['repo_url', 'required_paths'])
                self.assertTrue(tool.annotations.readOnlyHint)
                result = await session.call_tool('check_public_repo', {
                    'repo_url': 'https://invalid.example/a/b', 'required_paths': ['README.md']})
                self.assertFalse(result.isError)
                self.assertTrue(result.structuredContent['errors'])
                self.assertEqual(result.structuredContent['missing'], [])
