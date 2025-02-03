import re

def _process_numbers(text: str) -> str:
    """处理数字格式
    
    Args:
        text: 输入文本
        
    Returns:
        处理后的文本
    """
    def _should_split_digits(match) -> bool:
        """判断是否应该分割数字"""
        number = match.group()
        context_before = text[max(0, match.start() - 20):match.start()]
        
        # 电话号码特征
        phone_patterns = [
            r'电话[号码]?[是为:：]?',
            r'联系[方式]?[是为:：]?',
            r'[致]?电[:]?',
            r'手机[号码]?',
            r'[致]?电话[:]?',
            r'Tel[:.：]?',
            r'TEL[:.：]?',
            r'Phone[:.：]?',
        ]
        
        # 检查前文是否包含电话号码相关特征
        for pattern in phone_patterns:
            if re.search(pattern, context_before):
                return True
                
        # 检查数字格式特征
        if '-' in number or len(number) in [7, 8, 11]:  # 常见电话号码长度
            return True
            
        return False

    # 处理带分隔符的号码 (如 022-12345678)
    text = re.sub(r'\d+[-\s]+\d+', 
                 lambda m: ' '.join(m.group()) if _should_split_digits(m) else m.group(), 
                 text)
    
    # 处理连续数字
    text = re.sub(r'\d+',
                 lambda m: ' '.join(m.group()) if _should_split_digits(m) else m.group(),
                 text)
    
    return text

def _process_urls(text: str) -> str:
    """处理URL
    
    Args:
        text: 输入文本
        
    Returns:
        处理后的文本
    """
    # 替换网址为"网址链接"
    text = re.sub(r'https?://[^\s<>"]+|www\.[^\s<>"]+', '网址链接', text)
    
    return text

def _process_symbols(text: str) -> str:
    """处理特殊符号
    
    Args:
        text: 输入文本
        
    Returns:
        处理后的文本
    """
    # 保留的常用标点符号
    preserved_symbols = [
        '。', '，', '、', '；', '：', '？', '！',  # 中文标点
        '—', '·',  # 其他中文常用符号
        '.', ',', ';', ':', '?', '!',  # 英文标点
        '"', '"', ''', ''',  # 引号
        '\n', '\r', '\t', ' '  # 空白字符
    ]
    
    # 构建正则表达式模式，排除保留的符号
    preserved_pattern = '|'.join(map(re.escape, preserved_symbols))
    
    # 特殊符号替换规则
    symbol_replacements = {
        r'@': '艾特',
        r'#': '井号',
        r'\$': '美元',
        r'%': '百分',
        r'&': '和',
        r'\+': '加',
        r'=': '等于',
        #r'~': '波浪号', # 移除波浪号的替换规则
        r'\^': '上尖号',
        r'\*': '星号',
        r'×': '乘以',
        r'÷': '除以',
        r'√': '根号',
        r'∑': '求和',
        r'∏': '求积',
        r'±': '正负',
        r'≠': '不等于',
        r'≤': '小于等于',
        r'≥': '大于等于',
        r'≈': '约等于',
        r'∞': '无穷',
        r'∵': '因为',
        r'∴': '所以',
        r'∠': '角',
        r'⊙': '圆',
        r'○': '圆',
        r'π': '派',
        r'∫': '积分',
        r'∮': '曲线积分',
        r'∪': '并集',
        r'∩': '交集',
        r'∈': '属于',
        r'∉': '不属于',
        r'⊆': '包含于',
        r'⊂': '真包含于',
        r'⊇': '包含',
        r'⊃': '真包含',
        r'∅': '空集',
        r'∀': '任意',
        r'∃': '存在',
        r'¬': '非',
        r'∧': '与',
        r'∨': '或',
        r'⇒': '推出',
        r'⇔': '等价于'
    }
    
    # 替换特殊符号
    for symbol, replacement in symbol_replacements.items():
        text = re.sub(symbol, replacement, text)
    
    # 移除其他所有特殊符号（保留指定的标点符号）
    text = re.sub(f'[^\\w\\s{preserved_pattern}]', '', text)
    
    return text

def clean_markdown(text: str) -> str:
    """清理Markdown格式"""
    # 移除代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # 移除行内代码
    text = re.sub(r'`[^`]*`', '', text)
    
    # 移除链接，保留链接文本
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    
    # 移除图片
    text = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', '', text)
    
    # 移除标题标记
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    
    # 移除粗体和斜体
    text = re.sub(r'\*\*([^\*]*)\*\*', r'\1', text)
    text = re.sub(r'\*([^\*]*)\*', r'\1', text)
    text = re.sub(r'__([^_]*)__', r'\1', text)
    text = re.sub(r'_([^_]*)_', r'\1', text)
    
    # 移除引用
    text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
    
    # 移除分隔线
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    
    # 移除列表标记
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # 移除括号及括号内内容
    text = re.sub(r'\(.*?\)', '', text)  # 英文括号
    text = re.sub(r'（.*?）', '', text)  # 中文括号
    
    # 移除 ~, ..., …
    text = re.sub(r'[~…]+', '', text)
    
    # 清理多余空白
    text = re.sub(r'\s*\n\s*', '。', text)  # 将换行替换为句号
    text = re.sub(r'。{2,}', '。', text)    # 合并多个句号
    text = text.strip()
    
    # 处理特殊格式
    text = _process_urls(text)      # 处理URL
    text = _process_numbers(text)   # 处理数字
    text = _process_symbols(text)   # 处理特殊符号
    
    return text