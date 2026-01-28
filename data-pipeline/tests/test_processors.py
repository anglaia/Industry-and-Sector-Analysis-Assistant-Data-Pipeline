"""
处理器测试
"""
import pytest
from processors.text_cleaner import TextCleaner
from processors.metadata_extractor import MetadataExtractor


class TestTextCleaner:
    """文本清洗器测试"""
    
    def test_clean_text(self):
        """测试基础文本清洗"""
        dirty_text = "This  is    a   test\n\n\nwith    extra    spaces"
        clean_text = TextCleaner.clean_text(dirty_text)
        
        assert "  " not in clean_text
        assert clean_text.startswith("This is a test")
    
    def test_remove_urls(self):
        """测试 URL 移除"""
        text = "Visit https://example.com for more info"
        clean_text = TextCleaner.remove_urls(text)
        
        assert "https://example.com" not in clean_text
        assert "Visit" in clean_text
    
    def test_remove_emails(self):
        """测试邮箱移除"""
        text = "Contact us at info@example.com"
        clean_text = TextCleaner.remove_emails(text)
        
        assert "info@example.com" not in clean_text
        assert "Contact us at" in clean_text


class TestMetadataExtractor:
    """元数据提取器测试"""
    
    def test_extract_year_from_filename(self):
        """测试从文件名提取年份"""
        filename = "AAPL_10-K_2023-12-31.pdf"
        metadata = MetadataExtractor.extract_from_filename(filename)
        
        assert metadata['year'] == '2023'
    
    def test_extract_industry_from_text(self):
        """测试从文本推断行业"""
        text = "This company develops software and provides cloud computing services..."
        industries = MetadataExtractor.extract_industry_from_text(text)
        
        assert 'Technology' in industries
    
    def test_extract_date_from_text(self):
        """测试从文本提取日期"""
        text = "Report published on 2023-12-31"
        date = MetadataExtractor.extract_date_from_text(text)
        
        assert date == "2023-12-31"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

