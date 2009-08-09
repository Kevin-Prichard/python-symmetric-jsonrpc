class ReIterator(object):
    def __init__(self, i):
        self.prefix = [] # In reverse order!
        self.i = iter(i)

    def __iter__(self):
        return self

    def next(self):
        if self.prefix:
            return self.prefix.pop()
        return self.i.next()

    def put(self, value):
        self.prefix.append(value)

    def peek(self):
        if not self.prefix:
            self.put(self.i.next())
        return self.prefix[-1]

class Reader(object):
    "An SAX-like recursive-descent parser for JSON."

    def __init__(self, s):
        self.s = ReIterator(s)
    
    # Override these in a subclass to actually do something with the
    # parsed data
    def pair_begin(self): pass
    def pair_end(self): pass
    def object_begin(self): pass
    def object_end(self): pass
    def array_begin(self): pass
    def array_end(self): pass
    def string_begin(self): pass
    def string_end(self): pass
    def number_begin(self): pass
    def number_end(self): pass
    def char(self, c): pass 
    def true(self): pass
    def false(self): pass
    def null(self): pass
    def fail(self, msg): pass

    def _assert(self, c, values):
        if c not in values:
            self.fail("<%s> not in <%s>" % (c, values))
        return c

    def _read_space(self):
        while self.s.peek() in ' \t\r\n':
            self.s.next()

    def _read_pair(self):
        self.pair_begin()
        self._read_string()
        self._read_space()
        self._assert(self.s.next(), ':')
        self._read_space()
        self._read_value()
        self.pair_end()
    
    def _read_object(self):
        self.object_begin()
        self._assert(self.s.next(), '{')
        self._read_space()
        if self.s.peek() != '}':
            while True:
                self._read_pair()
                self._read_space()
                if self.s.peek() == '}':
                    break
                self._assert(self.s.next(), ',')
                self._read_space()
        self._assert(self.s.next(), '}')
        self.object_end()
        
    def _read_array(self):
        self.array_begin()
        self._assert(self.s.next(), '[')
        self._read_space()
        if self.s.peek() != ']':
            while True:
                self._read_value()
                self._read_space()
                if self.s.peek() == ']':
                    break
                self._assert(self.s.next(), ',')
                self._read_space()
        self._assert(self.s.next(), ']')
        self.array_end()

    def _read_char(self):
        c = self.s.next()
        if c == '\\':
            c = self.s.next()
            if c == 'b': c = '\b'
            elif c == 'f': c = '\f'
            elif c == 'n': c = '\n'
            elif c == 'r': c = '\r'
            elif c == 't': c = '\t'
            elif c == 'u':
                d1 = self.s.next()
                d2 = self.s.next()
                d3 = self.s.next()
                d4 = self.s.next()
                c = unichr(int(d1+d2+d3+d4, 16))
            else: self._assert(c, '"\\/')
        self.char(c)

    def _read_string(self):
        self.string_begin()
        self._assert(self.s.next(), '"')
        while self.s.peek() != '"':
            self._read_char()
        self._assert(self.s.next(), '"')
        self.string_end()

    def _read_number(self):
        self.number_begin()
        if self.s.peek() == '-':
            self.char(self.s.next())
        if self.s.peek() == '0':
            self.char(self.s.next())
        else:
            self._assert(self.s.peek(), '123456789')
            self.char(self.s.next())
            while self.s.peek() in '0123456789':
                self.char(self.s.next())
        if self.s.peek() == '.':
            self.char(self.s.next())
            self._assert(self.s.peek(), '0123456789')
            while self.s.peek() in '0123456789':
                self.char(self.s.next())
        if self.s.peek() in 'eE':
            self.char(self.s.next())
            if self.s.peek() in '+-':
                self.char(self.s.next())
            self._assert(self.s.peek(), '0123456789')
            while self.s.peek() in '0123456789':
                self.char(self.s.next())
        self.number_end()

    def _read_true(self):
        self._assert(self.s.next(), 't')
        self._assert(self.s.next(), 'r')
        self._assert(self.s.next(), 'u')
        self._assert(self.s.next(), 'e')
        self.true()

    def _read_false(self):
        self._assert(self.s.next(), 'f')
        self._assert(self.s.next(), 'a')
        self._assert(self.s.next(), 'l')
        self._assert(self.s.next(), 's')
        self._assert(self.s.next(), 'e')
        self.true()

    def _read_null(self):
        self._assert(self.s.next(), 'n')
        self._assert(self.s.next(), 'u')
        self._assert(self.s.next(), 'l')
        self._assert(self.s.next(), 'l')
        self.null()

    def _read_value(self):
        c = self.s.peek()
        if c == '{': return self._read_object()
        elif c == '[': return self._read_array()
        elif c == '"': return self._read_string()
        elif c == 't': return self._read_true()
        elif c == 'f': return self._read_false()
        elif c == 'n': return self._read_null()
        else: return self._read_number()

    def read_value(self):
        return self._read_value()

    def read_values(self):
        while True:
            self._read_value()    

class ParserReader(Reader):
    def _struct_begin(self):
        self.state.append([])
    def _struct_end(self):
        self.state[-2].append(self.state[-1])
        del self.state[-1]
    def pair_begin(self): self._struct_begin()
    def pair_end(self): self._struct_end()
    def object_begin(self): self._struct_begin()
    def object_end(self):
        self.state[-1] = dict(self.state[-1])
        self._struct_end()
    def array_begin(self): self._struct_begin()
    def array_end(self): self._struct_end()
    def string_begin(self): self.state.append(u"")
    def string_end(self):  self._struct_end()
    def number_begin(self): self.state.append(u"")
    def number_end(self):
        if '.' in self.state[-1]:
            self.state[-1] = float(self.state[-1]) 
        else:
            self.state[-1] = int(self.state[-1])
        self._struct_end()
    def char(self, c): self.state[-1] = self.state[-1] + c
    def true(self): self.state[-1].append(True)
    def false(self): self.state[-1].append(False)
    def null(self): self.state[-1].append(None)
    def fail(self, msg): raise Exception(msg)
    def read_value(self):
        self.state = [[]]
        self._read_value()
        return self.state[-1][-1]
    def read_values(self):
        while True:
            self.state = [[]]
            self._read_value()    
            yield self.state[-1][-1]        

class DebugReader(object):
    def pair_begin(self): print '('; print self.state; return super(DebugReader, self).pair_begin()
    def pair_end(self): print ')'; print self.state; return super(DebugReader, self).pair_end()
    def object_begin(self): print '{'; print self.state; return super(DebugReader, self).object_begin()
    def object_end(self): print '}'; print self.state; return super(DebugReader, self).object_end()
    def array_begin(self): print '['; print self.state; return super(DebugReader, self).array_begin()
    def array_end(self): print ']'; print self.state; return super(DebugReader, self).array_end()
    def string_begin(self): print '"'; print self.state; return super(DebugReader, self).string_begin()
    def string_end(self): print '"'; print self.state; return super(DebugReader, self).string_end()
    def number_begin(self): print '<'; print self.state; return super(DebugReader, self).number_begin()
    def number_end(self): print '>'; print self.state; return super(DebugReader, self).number_end()
    def char(self, c): print repr(c); print self.state; return super(DebugReader, self).char(c)
    def true(self): print "TRUE"; print self.state; return super(DebugReader, self).true()
    def false(self): print "FALSE"; print self.state; return super(DebugReader, self).false()
    def null(self): print "NULL"; print self.state; return super(DebugReader, self).null()
    def fail(self, msg): super(DebugReader, self).fail(); raise Exception(msg)

class MyReader(DebugReader, ParserReader): pass


if __name__ == "__main__":
    import sys
    try:
        print MyReader(sys.argv[1]).read_value()
    except:
        import sys, pdb
        sys.last_traceback = sys.exc_info()[2]
        pdb.pm()