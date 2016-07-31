'''To be used in a with statement
'''

from contextlib import suppress

class Context:

    def __init__(self, content={}):
        self.subjects = []
        self.content  = content

    def __enter__(self):
        'afesgs'

    def __exit__(self, exc_type, exc_value, traceback):
        'awd'
        for obj in self.subjects:
            for key,val in self.content.items():
                with suppress(AttributeError): obj.context = None

    async def __aenter__(self):
        'arghth'
        Context.__enter__(self, exc_type, exc_value, traceback)

    async def __aexit__(self, exc_type, exc_value, traceback):
        'asdfr'
        Context.__exit__(self, exc_type, exc_value, traceback)
        # why not async for? Think of this as an "atomic" unlock. We want to
        # avoid intersecting contexts, i.e. maintain concurrency. If yielding
        # we'd be outside the context before finishing the exit.

    def use(self, *objs):
        'docstring'
        for obj in objs:
            self.subjects.append(obj)
            for key,val in self.content.items():
                with suppress(AttributeError): obj[key] = val
        return self



if __name__ == '__main__':
    class Tester:
        def __init__(self): self.foo = None
    obj = Tester()
    context = Context({"foo":42})
    with Context().use(obj, 'idonthavefoo'):
        print(obj.foo)
    print(obj.foo)
