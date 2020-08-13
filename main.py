# coding=utf-8
"""
给日志文件加标签, 能折叠以及在vscode大纲显示结构
支持单行注释
支持标签属性, 目前有: 时间差计算
分支功能??
如果某个函数的结束日志异常, 会导致: 
"""
import re, sys
import datetime

def getTimeInterval(lines, cur, pre):
	pattern = re.compile(r'\[(\d\d:\d\d:\d\d)\]')
	match = re.search(pattern, lines[cur])
	if not match:
		return ""
	end_time = datetime.datetime.strptime(match.expand(r'\1'), "%H:%M:%S")
	match = re.search(pattern, lines[pre])
	if not match:
		return ""
	begin_time = datetime.datetime.strptime(match.expand(r'\1'), "%H:%M:%S")
	interval = (end_time - begin_time).seconds
	return " interval=\"%ss\"" % interval

def betweenLines(record, cur, pre):
	if cur == pre:
		return ""
	return " between=\"%d\"" % (cur - pre)


configure = [
	{
		"begin" : r'process (\d+) begin'
		, "end" : r'process \1 end'
		, "annotation" : r'处理消息.\1'
		, "attrs" : [ getTimeInterval ]
	}
	, {
		"begin" : r'connect to database (\w+) (\d+)'
		, "end" : r'disconnect database'
		, "annotation" : r'操作\1数据库\2'
	}
	, {
		"oneline" : r'xxxx'
		, "annotation" : r'单行注释'
		, "attrs" : [ getTimeInterval, betweenLines ]
	}
]

class Record():
	def __init__(self):
		self.end_pattern = ""
		self.tag = ""
		self.row = 0
		self.func = []

class LogParser():
	def __init__(self, srcFile):
		self.srcFile = srcFile
		self.lines = []
		self.stack = []
		self.dict = {}
		self.depth = 0
	
	def appendAttrs(self, record, row):
		attrs = ""
		for attrFunc in record.func:
			attrs += attrFunc(self.lines, row, record.row)
		return attrs			# 标签头设置属性

	def parse(self, rules):
		for row in range(len(self.lines)):
			if self.depth > 0:
				record = self.stack[-1]
				match_end = re.search(record.end_pattern, self.lines[row])
				if match_end:
					attrs = self.appendAttrs(record, row)
					self.lines[record.row] = self.lines[record.row] % attrs			# 标签头设置属性
					self.lines[row] = "%s</L%d.%s>\n" % (self.lines[row], self.depth, record.tag)	# 标签尾
					self.stack.pop(-1)
					self.depth -= 1
					continue
			for cfg in rules:
				if "oneline" in cfg:
					pattern = cfg["oneline"]
					match_oneline = re.search(pattern, self.lines[row])
					if match_oneline:
						if pattern not in self.dict:
							record = Record()
							record.row = 0
							record.func = cfg["attrs"] if ("attrs" in cfg) else []
							self.dict[pattern] = record
						attrs = self.appendAttrs(self.dict[pattern], row)
						self.lines[row] = "<%s%s/>\n%s" % (match_oneline.expand(cfg["annotation"]), attrs, self.lines[row])
						self.dict[pattern].row = row
						continue
				elif "begin" in cfg:
					match_begin = re.search(cfg["begin"], self.lines[row])
					if match_begin:
						record = Record()
						record.end_pattern = match_begin.expand(cfg["end"])		# 结束行匹配
						record.tag = match_begin.expand(cfg["annotation"])		# xml标签名
						record.func = cfg["attrs"] if ("attrs" in cfg) else []
						record.row = row
						self.stack.append(record)
						self.depth += 1
						self.lines[row] = "<L%d.%s%s>\n%s" % (self.depth, record.tag, "%s", self.lines[row])
						continue

	def readFromFile(self):
		rfd = open(self.srcFile, 'r')
		self.lines = rfd.readlines()
		rfd.close()

	def writeToFile(self, dstFile=None):
		if not dstFile:
			dstFile = "%s.xml" % self.srcFile
		wfd = open(dstFile, 'w')
		wfd.writelines(self.lines)
		wfd.close()

if __name__ == "__main__":
	# if len(sys.argv) != 2:
	# 	print('Error param')
	# 	exit(0)	
	# src_file = sys.argv[1]

	logParser = LogParser('test.log')
	logParser.readFromFile()
	logParser.parse(configure)
	logParser.writeToFile()
	



