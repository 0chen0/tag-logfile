# coding=utf-8
"""
给日志文件加标签, 能折叠以及在vscode大纲显示结构
python ./main.py ./test.log > ./result.xml
"""
import re, sys
import datetime

configure = [
	{
		"begin" : r'process (\d+) begin'
		, "end" : r'process \1 end'
		, "annotation" : r'处理消息.\1'
	}
	, {
		"begin" : r'connect to database (\w+) (\d+)'
		, "end" : r'disconnect database'
		, "annotation" : r'操作\1数据库\2'
	}
	, {
		"oneline" : r'xxxx'
		, "annotation" : r'单行注释'
	}
]

def getTimeInterval(begin, end):
	pattern = re.compile(r'\[(\d\d:\d\d:\d\d)\]')
	match = re.search(pattern, end)
	if not match:
		return ""
	end_time = datetime.datetime.strptime(match.expand(r'\1'), "%H:%M:%S")
	match = re.search(pattern, begin)
	if not match:
		return ""
	begin_time = datetime.datetime.strptime(match.expand(r'\1'), "%H:%M:%S")
	interval = (end_time - begin_time).seconds
	return " interval=\"%ss\"" % interval


class Record():
	def __init__(self):
		self.end_pattern = ""
		self.tag = ""
		self.row = 0

class LogParser():
	def __init__(self, srcFile, attrsFunc=None):
		self.srcFile = srcFile
		self.attrsFunc = attrsFunc
		self.lines = []
		self.stack = []
		self.depth = 0
	
	def parse(self, rules):
		for row in range(len(self.lines)):
			if self.depth > 0:
				record = self.stack[-1]
				match_end = re.search(record.end_pattern, self.lines[row])
				if match_end:
					attrs = ""
					for attrFunc in self.attrsFunc:
						attrs += attrFunc(self.lines[record.row], self.lines[row])
					self.lines[record.row] = self.lines[record.row] % attrs			# 标签头设置属性
					self.lines[row] = "%s</L%d.%s>\n" % (self.lines[row], self.depth, record.tag)	# 标签尾
					self.stack.pop(-1)
					self.depth -= 1
					continue
			for cfg in rules:
				if "oneline" in cfg:
					match_oneline = re.search(cfg["oneline"], self.lines[row])
					if match_oneline:
						self.lines[row] = "<%s/>\n%s" % (match_oneline.expand(cfg["annotation"]), self.lines[row])
						continue
				elif "begin" in cfg:
					match_begin = re.search(cfg["begin"], self.lines[row])
					if match_begin:
						record = Record()
						record.end_pattern = match_begin.expand(cfg["end"])		# 结束行匹配
						record.tag = match_begin.expand(cfg["annotation"])		# xml标签名
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

	logParser = LogParser('test.log', [getTimeInterval])
	logParser.readFromFile()
	logParser.parse(configure)
	logParser.writeToFile()
	



