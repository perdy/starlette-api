import functools
import multiprocessing

from flama import concurrency


async def task(event):
    event.set()


class TestCaseIsAsync:
    def test_function(self):
        def foo_sync():
            ...

        async def foo_async():
            ...

        assert not concurrency.is_async(foo_sync)
        assert concurrency.is_async(foo_async)

    def test_callable(self):
        class FooSync:
            def __call__(self):
                ...

        class FooAsync:
            async def __call__(self):
                ...

        assert not concurrency.is_async(FooSync)
        assert concurrency.is_async(FooAsync)

    def test_partial(self):
        def foo_sync(x: int):
            ...

        partial_foo_sync = functools.partial(foo_sync, x=1)

        async def foo_async(x: int):
            ...

        partial_foo_async = functools.partial(foo_async, x=1)

        assert not concurrency.is_async(partial_foo_sync)
        assert concurrency.is_async(partial_foo_async)


class TestCaseRun:
    async def test_async(self):
        async def foo_async(x: int):
            return x + 2

        assert await concurrency.run(foo_async, 3) == 5

    async def test_sync(self):
        def foo_sync(x: int):
            return x * 2

        assert await concurrency.run(foo_sync, 3) == 6


class TestCaseRunTaskGroup:
    async def test_run_task_group(self):
        expected_result = ["foo", "bar"]

        async def foo():
            return "foo"

        async def bar():
            return "bar"

        result = [t.result() for t in await concurrency.run_task_group(foo(), bar())]

        assert result == expected_result


class TestCaseAsyncProcess:
    async def test_async_process(self):
        event = multiprocessing.Event()

        process = concurrency.AsyncProcess(target=task, args=(event,))
        process.start()
        process.join()

        assert event.wait(1.0)
