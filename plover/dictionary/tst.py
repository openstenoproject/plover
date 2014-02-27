import Queue

class Node:
    def __init__ (self):
        self.c = None
        self.left = None
        self.mid = None
        self.right = None
        self.value = None

class TST:

    def __init__ (self):
        self.N = 0
        self.root = None

    def __len__(self):
        return self.N

    def get(self, key):
        if (key is None or key.__len__()==0):
            raise Exception("Null or empty key")
        x = self.get_i(self.root, key, 0)
        if x is None:
            return None
        return x.value

    def get_i(self, x, key, d):
        if (key is None or key.__len__()==0):
            raise Exception("Null or empty key")
        if x is None:
            return None
        c = key[d]
        if c < x.c:
            return self.get_i(x.left, key, d)
        elif c > x.c:
            return self.get_i(x.right, key, d)
        elif (d < key.__len__()-1):
            return self.get_i(x.mid, key, d+1)
        else:
            return x

    def contains(self, key):
        return not (self.get(key) is None)

    def put(self, s, val):
        if not self.contains(s):
            self.N +=1
        self.root = self.put_i(self.root, s, val, 0)

    def put_i(self, x, s, val, d):
        c = s[d]
        if x is None:
            x = Node()
            x.c = c
        if c < x.c:
            x.left = self.put_i(x.left, s, val, d)
        elif (c > x.c):
            x.right = self.put_i(x.right, s, val, d)
        elif (d < s.__len__()-1):
            x.mid = self.put_i(x.mid, s, val, d+1)
        else:
            x.value = val
        return x

    def longestPrefixOf(self, s):
        if (s is None or len(s) == 0):
            return ""
        length = 0
        x = self.root
        i = 0
        while (x) and (i < len(s)):
            c = s[i]
            if c < x.c:
                x = x.left
            elif c > x.c:
                x = x.right
            else:
                i+=1
                if not x.value is None:
                    length = i
                x = x.mid
        return s[0:length]

    def prefixMatch(self, prefix):
        x = self.get_i(self.root, prefix, 0)
        q = Queue.Queue(0)
        if (not x):
            return []
        if (not x.value):
            return q.put(prefix)
        self.collect_i(x.mid, prefix, q)
        return q

    def collect_i(self, x, prefix, queue):
        if x is None:
            return
        self.collect_i(x.left, prefix, queue)
        if (not x.value is None):
            queue.put(prefix + x.c)
        self.collect_i(x.mid, prefix + x.c, queue)
        self.collect_i(x.right, prefix, queue)

    def keys(self):
        q = Queue.Queue(0)
        self.collect_i(self.root, "", q)
        return q

    def collect_ii(self, x, prefix, i, pat, q):
        if x is None:
            return
        c = pat[i]
        if (c == '.') or (c < x.c):
            self.collect_ii(x.left, self.prefix, i, pat, q)
        if (c == '.') or (c == x.c):
            if (i == pat.__len__()-1) and (not x.value is None):
                q.put(prefix+x.c)
            if (i < pat.__len__()-1):
                self.collect_ii(x.mid, prefix + x.c, i+1, pat, q)
        if (c == '.') or (c > x.c):
            self.collect_ii(x.right, prefix, i, pat, q)

    def wildcardMatch(self, pat):
        q = Queue.Queue(0)
        self.collect_ii(self.root, "", 0, pat, q)
        return q
                
