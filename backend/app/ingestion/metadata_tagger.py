"""
Metadata tagger for Budget 2026 AI Platform
Tags chunks with: topic, user_type, sector, income_range for personalized retrieval
"""
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, asdict
import re

from ..core.logger import setup_logger, log_extra

logger = setup_logger(__name__)


@dataclass
class ChunkMetadata:
    """Enhanced metadata tags for a text chunk"""
    # Hierarchical topics
    topics: List[Dict[str, str]]  # [{main: "Taxation", sub: "Income Tax", section: "Salaried"}]
    
    # User types (flat - simpler)
    user_types: List[str]
    
    # Sectors (flat)
    sectors: List[str]
    
    # Normalized income ranges
    income_ranges: List[str]  # Standardized: 0-5L, 5-10L, 10-15L, 15L+
    
    # Keywords for hybrid search
    keywords: List[str]
    
    # Versioning
    pipeline_version: str = "v1.0"
    created_at: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MetadataTagger:
    """
    Rule-based metadata tagger using keyword matching
    Tags chunks for personalized retrieval
    """
    
    def __init__(self):
        """Initialize tagger with keyword dictionaries"""
        
        # Hierarchical topic structure
        self.topic_hierarchy = {
            'tax': {'main': 'Taxation', 'sub': 'Tax Policy'},
            'income_tax': {'main': 'Taxation', 'sub': 'Income Tax', 'section': 'Personal Tax'},
            'gst': {'main': 'Taxation', 'sub': 'GST'},
            'healthcare': {'main': 'Social Welfare', 'sub': 'Healthcare'},
            'education': {'main': 'Social Welfare', 'sub': 'Education'},
            'defense': {'main': 'National Security', 'sub': 'Defense'},
            'agriculture': {'main': 'Economic Development', 'sub': 'Agriculture'},
            'infrastructure': {'main': 'Economic Development', 'sub': 'Infrastructure'},
            'employment': {'main': 'Economic Development', 'sub': 'Employment'},
            'finance': {'main': 'Economic Policy', 'sub': 'Finance'},
            'social_welfare': {'main': 'Social Welfare', 'sub': 'General Welfare'},
            'energy': {'main': 'Economic Development', 'sub': 'Energy'},
            'digital': {'main': 'Technology', 'sub': 'Digital Infrastructure'},
            'msme': {'main': 'Economic Development', 'sub': 'MSME'}
        }
        
        # Normalized income ranges (standardized)
        self.normalized_income_ranges = ['0-5L', '5-10L', '10-15L', '15L+']
        
        # Topic keywords
        self.topic_keywords = {
            'tax': ['tax', 'taxation', 'income tax', 'gst', 'customs', 'excise', 'duty', 'cess', 
                   'surcharge', 'rebate', 'deduction', 'exemption', 'section 80', 'tds', 'tcs'],
            'healthcare': ['health', 'medical', 'hospital', 'ayushman', 'medicine', 'doctor',
                          'treatment', 'insurance', 'wellness', 'disease', 'vaccine'],
            'education': ['education', 'school', 'university', 'student', 'scholarship', 'learning',
                         'skill', 'training', 'research', 'academic'],
            'defense': ['defense', 'defence', 'military', 'army', 'navy', 'air force', 'security',
                       'border', 'weapon', 'soldier'],
            'agriculture': ['agriculture', 'farmer', 'crop', 'farming', 'irrigation', 'fertilizer',
                           'seed', 'rural', 'kisan', 'mandi', 'minimum support price', 'msp'],
            'infrastructure': ['infrastructure', 'road', 'highway', 'railway', 'metro', 'airport',
                              'port', 'bridge', 'construction', 'urban development'],
            'employment': ['employment', 'job', 'unemployment', 'wage', 'salary', 'epf', 'provident fund',
                          'pension', 'retirement', 'employee'],
            'finance': ['finance', 'banking', 'loan', 'credit', 'debt', 'fiscal', 'monetary',
                       'reserve bank', 'rbi', 'interest rate'],
            'social_welfare': ['welfare', 'subsidy', 'scheme', 'benefit', 'allowance', 'pension',
                              'poverty', 'below poverty line', 'bpl'],
            'energy': ['energy', 'power', 'electricity', 'renewable', 'solar', 'coal', 'oil',
                      'petroleum', 'gas', 'fuel'],
            'digital': ['digital', 'technology', 'it', 'software', 'cyber', 'internet', 'online',
                       'e-governance', 'digital india'],
            'msme': ['msme', 'small business', 'medium enterprise', 'startup', 'entrepreneur',
                    'mudra', 'sidbi']
        }
        
        # User type keywords
        self.user_type_keywords = {
            'salaried': ['salary', 'salaried', 'employee', 'employer', 'wage', 'profession',
                        'professional', 'employment', 'tds'],
            'business': ['business', 'trader', 'entrepreneur', 'proprietor', 'partnership',
                        'company', 'firm', 'gst', 'turnover'],
            'senior_citizen': ['senior citizen', 'senior', 'aged', 'elderly', 'pension',
                              '60 years', '80 years'],
            'student': ['student', 'education', 'scholarship', 'fee', 'tuition', 'school',
                       'college', 'university'],
            'farmer': ['farmer', 'agriculture', 'agricultural income', 'crop', 'kisan'],
            'woman': ['woman', 'women', 'female', 'maternity', 'maternal', 'girl child',
                     'beti bachao'],
            'disabled': ['disabled', 'disability', 'handicapped', 'differently abled', 'pwd'],
            'nri': ['nri', 'non-resident', 'foreign', 'overseas', 'expatriate']
        }
        
        # Sector keywords
        self.sector_keywords = {
            'it': ['information technology', 'software', 'it', 'tech', 'computer', 'digital'],
            'manufacturing': ['manufacturing', 'industry', 'factory', 'production', 'make in india'],
            'services': ['service', 'services', 'hospitality', 'tourism', 'consulting'],
            'agriculture': ['agriculture', 'farming', 'agri', 'crop', 'livestock'],
            'healthcare': ['healthcare', 'medical', 'pharmaceutical', 'hospital', 'clinical'],
            'education': ['education', 'educational', 'school', 'coaching', 'training'],
            'real_estate': ['real estate', 'property', 'housing', 'construction', 'builder'],
            'finance': ['banking', 'finance', 'insurance', 'investment', 'nbfc'],
            'retail': ['retail', 'shop', 'store', 'mall', 'e-commerce'],
            'transport': ['transport', 'logistics', 'shipping', 'delivery', 'courier']
        }
        
        # Normalized income range keywords (INR in lakhs)
        self.income_keywords = {
            '0-5L': ['up to', 'below 5 lakh', 'less than 5 lakh', 'upto 5 lakh',
                    'not exceeding 5 lakh', '2.5 lakh', '3 lakh', '5 lakh'],
            '5-10L': ['5 lakh to 10 lakh', '7 lakh', '7.5 lakh', '10 lakh',
                     'between 5 and 10 lakh', 'above 5 lakh', 'exceeding 5 lakh'],
            '10-15L': ['10 lakh to 15 lakh', '12 lakh', '12.5 lakh', '15 lakh',
                      'between 10 and 15 lakh', 'above 10 lakh'],
            '15L+': ['above 15 lakh', 'exceeding 15 lakh', '20 lakh', '50 lakh', '1 crore',
                    'more than 15 lakh', 'super rich', 'high income']
        }
        
        logger.info("Initialized MetadataTagger with keyword dictionaries")
    
    def _find_matches(self, text: str, keyword_dict: Dict[str, List[str]]) -> List[str]:
        """
        Find which categories match based on keywords
        
        Args:
            text: Text to search
            keyword_dict: Dictionary of category -> keywords
            
        Returns:
            List of matching categories
        """
        text_lower = text.lower()
        matches = []
        
        for category, keywords in keyword_dict.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matches.append(category)
                    break  # Found match for this category
        
        return matches
    
    def _to_hierarchical_topics(self, flat_topics: List[str]) -> List[Dict[str, str]]:
        """
        Convert flat topic tags to hierarchical structure
        
        Args:
            flat_topics: List of flat topic names
            
        Returns:
            List of hierarchical topic dictionaries
        """
        hierarchical = []
        
        for topic in flat_topics:
            if topic in self.topic_hierarchy:
                hierarchical.append(self.topic_hierarchy[topic])
            else:
                # Fallback for unknown topics
                hierarchical.append({
                    'main': 'General',
                    'sub': topic.replace('_', ' ').title()
                })
        
        return hierarchical
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract important keywords from text
        Simple frequency-based extraction
        """
        # Remove common stop words
        stop_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
            'is', 'are', 'was', 'were', 'been', 'has', 'had', 'can', 'may', 'shall'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())
        
        # Filter and count
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]
    
    def tag_chunk(self, chunk_text: str) -> ChunkMetadata:
        """
        Tag a text chunk with enhanced metadata
        
        Args:
            chunk_text: Text to tag
            
        Returns:
            ChunkMetadata object with hierarchical topics
        """
        from datetime import datetime
        
        # Find flat matches first
        flat_topics = self._find_matches(chunk_text, self.topic_keywords)
        user_types = self._find_matches(chunk_text, self.user_type_keywords)
        sectors = self._find_matches(chunk_text, self.sector_keywords)
        income_ranges = self._find_matches(chunk_text, self.income_keywords)
        keywords = self._extract_keywords(chunk_text)
        
        # Convert to hierarchical topics
        hierarchical_topics = self._to_hierarchical_topics(flat_topics)
        
        # If no topics found, default to 'general'
        if not hierarchical_topics:
            hierarchical_topics = [{'main': 'General', 'sub': 'Uncategorized'}]
        
        return ChunkMetadata(
            topics=hierarchical_topics,
            user_types=user_types,
            sectors=sectors,
            income_ranges=sorted(income_ranges),  # Sort for consistency
            keywords=keywords,
            pipeline_version="v1.0",
            created_at=datetime.now().isoformat()
        )
    
    def tag_chunks(self, chunks: List) -> List[Dict]:
        """
        Tag multiple chunks
        
        Args:
            chunks: List of TextChunk objects
            
        Returns:
            List of dictionaries with chunk data + metadata
        """
        logger.info(
            f"Tagging {len(chunks)} chunks with metadata",
            extra=log_extra(chunk_count=len(chunks))
        )
        
        result = []
        
        for chunk in chunks:
            metadata = self.tag_chunk(chunk.text)
            
            # Combine chunk data with metadata
            chunk_with_metadata = {
                **chunk.to_dict(),
                'metadata': metadata.to_dict()
            }
            
            result.append(chunk_with_metadata)
        
        # Log statistics
        all_topics = set()
        all_user_types = set()
        
        for item in result:
            # Extract main topics from hierarchical structure
            for topic in item['metadata']['topics']:
                all_topics.add(topic.get('main', 'General'))
            all_user_types.update(item['metadata']['user_types'])
        
        logger.info(
            "Metadata tagging completed",
            extra=log_extra(
                chunks_tagged=len(result),
                unique_topics=len(all_topics),
                unique_user_types=len(all_user_types),
                topics=list(all_topics),
                user_types=list(all_user_types)
            )
        )
        
        return result


# Convenience function
def tag_document_chunks(chunks_by_doc: Dict[str, List]) -> Dict[str, List[Dict]]:
    """
    Tag chunks from multiple documents
    
    Args:
        chunks_by_doc: Dictionary mapping filename to list of chunks
        
    Returns:
        Dictionary mapping filename to list of tagged chunks
    """
    tagger = MetadataTagger()
    
    result = {}
    total_chunks = 0
    
    for filename, chunks in chunks_by_doc.items():
        tagged_chunks = tagger.tag_chunks(chunks)
        result[filename] = tagged_chunks
        total_chunks += len(tagged_chunks)
    
    logger.info(
        "Batch metadata tagging completed",
        extra=log_extra(
            documents=len(chunks_by_doc),
            total_chunks=total_chunks
        )
    )
    
    return result


if __name__ == "__main__":
    # Test the tagger
    print("🏷️  Testing Metadata Tagger\n")
    
    sample_text = """
    The Finance Bill proposes to amend the Income Tax Act to provide tax relief 
    for salaried employees earning up to 7 lakh rupees annually. Under the new 
    regime, individuals will benefit from reduced tax rates and increased standard 
    deduction. This will particularly help middle-class taxpayers and young professionals 
    in the IT sector.
    """
    
    tagger = MetadataTagger()
    metadata = tagger.tag_chunk(sample_text)
    
    print("Sample text tagged:")
    print(f"Topics: {metadata.topics}")
    print(f"User Types: {metadata.user_types}")
    print(f"Sectors: {metadata.sectors}")
    print(f"Income Ranges: {metadata.income_ranges}")
    print(f"Keywords: {metadata.keywords}")
