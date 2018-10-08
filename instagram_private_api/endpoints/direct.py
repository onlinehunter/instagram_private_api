import json
import time

from ..compat import (
    compat_urllib_error, compat_urllib_request,
    compat_http_client
)
from ..errors import ErrorHandler, ClientConnectionError
from ..http import MultipartFormDataEncoder
from socket import timeout, error as SocketError
from ssl import SSLError
try:
    ConnectionError = ConnectionError       # pylint: disable=redefined-builtin
except NameError:  # Python 2:
    class ConnectionError(Exception):
        pass


class DirectMiscEndpointsMixin(object):

    def _prepare_recipients(self, users_ids, thread_id=None, use_quotes=False):
        if not isinstance(users_ids, list):
            print('Users must be an list')
            return False
        result = {'users': '[[{}]]'.format(','.join(users_ids))}
        if thread_id:
            template = '["{}"]' if use_quotes else '[{}]'
            result['thread'] = template.format(thread_id)
        return result

    def send_direct_item(self, item_type, users_ids, **options):
        data = {
            'client_context': self.generate_uuid(),
            'action': 'send_item',
        }

        url = 'direct_v2/threads/broadcast/{}/'.format(item_type)
        text = options.get('text', '')
        if item_type == 'link':
            data['link_text'] = text
            data['link_urls'] = json.dumps(options.get('urls'))
        elif item_type == 'text':
            data['text'] = text
        elif item_type == 'media_share':
            data['text'] = text
            data['media_type'] = options.get('media_type', 'photo')
            data['media_id'] = options.get('media_id', '')
        elif item_type == 'hashtag':
            data['text'] = text
            data['hashtag'] = options.get('hashtag', '')
        elif item_type == 'profile':
            data['text'] = text
            data['profile_user_id'] = options.get('profile_user_id')

        recipients = self._prepare_recipients(users_ids, options.get('thread'), use_quotes=False)
        if not recipients:
            return False
        data['recipient_users'] = recipients.get('users')
        if recipients.get('thread'):
            data['thread_ids'] = recipients.get('thread')

        return self._call_api(url, params=data, unsigned=True)

    def send_direct_photo(self, photo_data, users_ids, **options):
        upload_id = options.get('upload_id', str(int(time.time() * 1000)))
        data = [
            ['client_context', self.generate_uuid()],
            ['action', 'send_item'],
            ['upload_id', upload_id],
        ]
        recipients = self._prepare_recipients(users_ids, options.get('thread'), use_quotes=False)
        if not recipients:
            return False
        data.append(['recipient_users', recipients.get('users')])
        if recipients.get('thread'):
            data.append(['thread_ids', recipients.get('thread')])

        url = 'direct_v2/threads/broadcast/upload_photo/'

        files = [
            ('photo', 'direct_temp_photo_{0!s}{1!s}'.format(upload_id, '.jpg'),
             'application/octet-stream', photo_data)
        ]

        content_type, body = MultipartFormDataEncoder().encode(data, files)
        headers = self.default_headers
        headers['Content-Type'] = content_type
        headers['Content-Length'] = len(body)

        url = '{0}{1}'.format(self.api_url.format(version='v1'), url)
        req = compat_urllib_request.Request(url, body, headers=headers)
        try:
            self.logger.debug('POST {0!s}'.format(url))
            response = self.opener.open(req, timeout=self.timeout)
        except compat_urllib_error.HTTPError as e:
            error_response = self._read_response(e)
            self.logger.debug('RESPONSE: {0:d} {1!s}'.format(e.code, error_response))
            ErrorHandler.process(e, error_response)
        except (SSLError, timeout, SocketError,
                compat_urllib_error.URLError,   # URLError is base of HTTPError
                compat_http_client.HTTPException) as connection_error:
            raise ClientConnectionError('{} {}'.format(
                connection_error.__class__.__name__, str(connection_error)))

        post_response = self._read_response(response)
        self.logger.debug('RESPONSE: {0:d} {1!s}'.format(response.code, post_response))
        json_response = json.loads(post_response)

        return json_response

    def get_inbox(self, cursor_id=None):
        endpoint = 'direct_v2/inbox/'
        query_params = {
            'persistentBadging': True,
            'use_unified_inbox': True
        }
        if cursor_id is not None:
            query_params['cursor'] = cursor_id

        return self._call_api(endpoint, query=query_params)

    def get_thread(self, thread_id, cursor_id=None):
        endpoint = 'direct_v2/threads/{thread_id:s}/'.format(**{'thread_id': thread_id})
        query_params = {
            'use_unified_inbox': True
        }

        if cursor_id is not None:
            query_params['cursor'] = cursor_id

        return self._call_api(endpoint, query=query_params)
