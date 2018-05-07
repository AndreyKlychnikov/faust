import re
from unittest.mock import Mock
import pytest
from mode.utils.futures import done_future


class test_Topic:

    @pytest.fixture
    def topic(self, *, app):
        return app.topic('foo')

    @pytest.fixture
    def message(self):
        return Mock(name='message')

    def test_on_published(self, *, topic):
        fut = Mock(name='fut')
        message = Mock(name='message')
        topic._on_published(fut, message)
        fut.result.assert_called_once_with()
        message.set_result.assert_called_once_with(fut.result())
        message.message.callback.assert_called_once_with(message)
        message.message.callback = None
        topic._on_published(fut, message)

    def test_aiter_when_iterator(self, *, topic):
        topic.is_iterator = True
        assert topic.__aiter__() is topic

    @pytest.mark.asyncio
    async def test_decode(self, *, topic, message):
        topic._compile_decode = Mock(name='_compile_decode')
        decode = topic._compile_decode.return_value
        decode.return_value = done_future()

        await topic.decode(message, propagate=True)
        topic._compile_decode.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_put(self, *, topic):
        topic.is_iterator = True
        topic.queue.put = Mock(name='queue')
        topic.queue.put.return_value = done_future('foo')
        event = Mock(name='event')
        await topic.put(event)
        topic.queue.put.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_put__raise_when_not_iterator(self, *, topic):
        topic.is_iterator = False
        with pytest.raises(RuntimeError):
            await topic.put(Mock(name='event'))

    def test_set_pattern__raise_when_topics(self, *, topic):
        topic.topics = ['A', 'B']
        with pytest.raises(TypeError):
            topic.pattern = re.compile('something.*')

    def test_set_partitions__raise_when_zero(self, *, topic):
        with pytest.raises(ValueError):
            topic.partitions = 0

    def test_derive_topic__raise_when_no_sub(self, *m, topic):
        topic.topics = None
        topic.pattern = None
        with pytest.raises(TypeError):
            topic.get_topic_name()

    def test_derive_topic__raise_if_pattern_and_prefix(self, *, topic):
        topic.topics = None
        topic.pattern = re.compile('something2.*')
        with pytest.raises(ValueError):
            topic.derive_topic(suffix='-repartition')

    def test_get_topic_name__raise_when_pattern(self, *, topic):
        topic.topics = None
        topic.pattern = re.compile('^foo.$')
        with pytest.raises(TypeError):
            topic.get_topic_name()

    def test_get_topic_name__raise_if_multitopic(self, *, topic):
        topic.topics = ['t1', 't2']
        with pytest.raises(ValueError):
            topic.get_topic_name()
