# -*- coding: utf-8 -*-
# 


class Main(object):
    data = "main default"

    def __init__(self):
        print self.data

    def test(self):
        return self.data


class Second(Main):
    data = "second default"

    def __init__(self):
        print self.data

    def test2(self):
        return self.data

    def test3(self):
        return super(Second, self).data


if __name__ == '__main__':
    m = Main()
    s = Second()

    print "m.test = %s" % m.test()
    print "s.test = %s" % s.test()
    print "s.test2 = %s" % s.test2()
    print "s.test3 = %s" % s.test3()
