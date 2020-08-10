# coding=utf-8
"""
给日志文件加标签, 能折叠以及在vscode大纲显示结构
python ./main.py ./test.log > ./result.xml
"""
import re, sys

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
]

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print('Error param')
		exit(0)
	
	src_file = sys.argv[1]
	file = open(src_file, 'r')

	_stack = []
	_tail = []
	_len = 0
	for line in file.readlines():
		if _len > 0 and _stack[_len-1]:
			match_end = re.search(_stack[_len-1], line)
			if match_end:
				sys.stdout.write("%s</L%d.%s>\n" % (line, _len, _tail[_len-1]))
				_stack.pop(-1)
				_tail.pop(-1)
				_len -= 1
				continue
		for cfg in configure:
			match_begin = re.search(cfg["begin"], line)
			if match_begin:
				pattern_end = match_begin.expand(cfg["end"])
				tag = match_begin.expand(cfg["annotation"])
				_stack.append(pattern_end)
				_tail.append(tag)
				_len += 1
				sys.stdout.write("<L%d.%s>\n" % (_len, tag))
				continue
		sys.stdout.write(line)
