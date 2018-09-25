import json


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


