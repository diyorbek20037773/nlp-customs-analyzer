import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import io
import re
import time
import random
from datetime import datetime
from urllib.parse import quote_plus
import json
from typing import List, Dict, Tuple, Optional
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Download required NLTK data with error handling
@st.cache_resource
def download_nltk_data():
    """Download NLTK data with caching"""
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
        return True
    except LookupError:
        try:
            with st.spinner("NLTK ma'lumotlari yuklab olinmoqda..."):
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('wordnet', quiet=True)
            return True
        except Exception as e:
            st.error(f"NLTK ma'lumotlarini yuklab olishda xatolik: {e}")
            return False

# Initialize NLTK
nltk_ready = download_nltk_data()

# Sahifa konfiguratsiyasi
st.set_page_config(
    page_title="Tovar tavsifi to'ldirish - Bojxona uchun",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stillar
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f4e79;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .highlight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .completeness-high {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .completeness-medium {
        background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .completeness-low {
        background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2e7bcf;
    }
    .analysis-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .enhancement-card {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        color: #1565c0;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    .source-card {
        background: #fff3e0;
        color: #e65100;
        padding: 0.8rem;
        border-radius: 6px;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ========================= PRODUCT DESCRIPTION ENHANCER =========================

class ProductDescriptionEnhancer:
    """Professional product description enhancer for customs officials"""
    
    def __init__(self):
        # Initialize NLTK components with error handling
        try:
            if nltk_ready:
                self.lemmatizer = WordNetLemmatizer()
                self.stop_words = set(stopwords.words('english'))
                self.nltk_available = True
            else:
                self.nltk_available = False
                self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'under', 'over', 'within', 'without', 'along', 'following', 'across', 'behind', 'beyond', 'plus', 'except', 'but', 'up', 'out', 'off', 'down', 'under', 'again', 'further', 'then', 'once'])
        except Exception as e:
            self.nltk_available = False
            self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
            st.warning(f"NLTK yuklanmadi, oddiy rejimda ishlaydi: {e}")
        
        # Essential information categories for customs
        self.essential_info_categories = {
            'brand': {
                'patterns': [
                    r'\b(apple|samsung|huawei|xiaomi|oppo|vivo|oneplus|google|sony|lg|nokia|motorola|realme|asus|acer|hp|dell|lenovo|msi|razer|alienware|microsoft|surface|bmw|mercedes|audi|toyota|honda|ford|volkswagen|hyundai|tesla|mazda|nissan|kia|lexus|porsche|jaguar|volvo|nike|adidas|puma|reebok|new balance|converse|vans|under armour|fila|gucci|prada|louis vuitton|chanel|hermes|versace|armani|calvin klein|tommy hilfiger|zara|h&m|uniqlo|gap|coca cola|pepsi|nestlé|unilever|procter|gamble|johnson|dove|loreal|maybelline|revlon|mac|clinique|estee lauder|lancome|dior|chanel|ysl|tom ford|rolex|omega|seiko|casio|citizen|tissot|tag heuer|breitling|cartier|chopard|bulgari|tiffany|pandora|swarovski|canon|nikon|fujifilm|olympus|panasonic|leica|pentax|gopro|dji|zhiyun|rode|bose|sennheiser|audio technica|beats|jbl|harman kardon|marshall|klipsch|polk|yamaha|pioneer|kenwood|alpine|focal|b&w|kef|q acoustics|monitor audio|elac|definitive technology|svs|rel|velodyne|paradigm|pmc|tannoy|spendor|proac|harbeth|wilson audio|magico|focal|dynaudio|b&w|kef|monitor audio|elac|definitive technology|svs|rel|velodyne|paradigm|pmc|tannoy|spendor|proac|harbeth|wilson audio|magico|focal|dynaudio)\b',
                    r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
                ],
                'weight': 25
            },
            'model': {
                'patterns': [
                    r'\b(iphone\s+\d+\s*(?:pro|max|plus|mini|se)?)\b',
                    r'\b(galaxy\s+[a-z]+\d+\s*(?:ultra|plus|pro)?)\b',
                    r'\b(pixel\s+\d+\s*(?:pro|xl)?)\b',
                    r'\b(macbook\s+(?:air|pro)\s*\d*)\b',
                    r'\b(surface\s+(?:pro|laptop|book|studio)\s*\d*)\b',
                    r'\b(ipad\s+(?:pro|air|mini)?\s*\d*)\b',
                    r'\b(watch\s+(?:series|se)\s*\d*)\b',
                    r'\b([a-z]+\s+[a-z0-9]+\s*(?:pro|max|ultra|plus|lite|se|air|mini)?)\b'
                ],
                'weight': 20
            },
            'technical_specs': {
                'patterns': [
                    r'\b(\d+)\s*(gb|tb|mb)\s*(?:ram|memory|storage|ssd|hdd|rom)?\b',
                    r'\b(\d+\.?\d*)\s*(inch|"|\')\s*(?:display|screen|monitor)?\b',
                    r'\b(\d+)\s*(mp|megapixel|megapixels)\s*(?:camera)?\b',
                    r'\b(\d+)\s*(mah|wh|hours?)\s*(?:battery)?\b',
                    r'\b(\d+)\s*(hz|ghz|mhz)\s*(?:refresh|processor|cpu)?\b',
                    r'\b(\d+)\s*(core|cores)\s*(?:processor|cpu)?\b',
                    r'\b(\d+k|4k|8k|uhd|hd|full hd|qhd)\b',
                    r'\b(wifi|bluetooth|5g|4g|lte|3g|nfc|usb|hdmi|ethernet|wi-fi)\b',
                    r'\b(android|ios|windows|macos|linux|chrome os)\s*(\d+\.?\d*)?\b',
                    r'\b(amoled|oled|lcd|led|qled|ips|tn|va|retina|super retina)\b'
                ],
                'weight': 30
            },
            'physical_attributes': {
                'patterns': [
                    r'\b(black|white|red|blue|green|yellow|orange|purple|pink|gray|grey|silver|gold|rose|bronze|copper|titanium|platinum|space|midnight|starlight|alpine|sierra|pacific|phantom|mystic|prism|aura|gradient|matte|glossy|transparent|clear|frosted)\b',
                    r'\b(\d+\.?\d*)\s*(kg|g|pounds?|lbs?|oz)\s*(?:weight)?\b',
                    r'\b(\d+\.?\d*)\s*(mm|cm|m|inches?|ft|feet)\s*(?:length|width|height|depth|diameter|size)?\b',
                    r'\b(\d+\.?\d*)\s*(l|ml|liters?|litres?|gallons?|fl oz|cups?)\s*(?:capacity|volume)?\b',
                    r'\b(leather|silicone|metal|aluminum|steel|plastic|glass|ceramic|carbon|titanium|rubber|fabric|wood|bamboo|stone|marble|granite)\b'
                ],
                'weight': 15
            },
            'category_identifiers': {
                'patterns': [
                    r'\b(smartphone|phone|mobile|cellular|handset|device)\b',
                    r'\b(laptop|notebook|computer|pc|desktop|workstation|ultrabook|chromebook|macbook)\b',
                    r'\b(tablet|ipad|slate|e-reader|kindle)\b',
                    r'\b(television|tv|monitor|display|smart tv|led tv|oled tv)\b',
                    r'\b(camera|dslr|mirrorless|camcorder|webcam|action cam|security cam)\b',
                    r'\b(headphones|earphones|earbuds|headset|speakers|soundbar|audio)\b',
                    r'\b(watch|smartwatch|fitness tracker|wearable|band|strap)\b',
                    r'\b(car|vehicle|automobile|sedan|suv|hatchback|coupe|truck|van|motorcycle|bike|scooter)\b',
                    r'\b(shirt|t-shirt|pants|jeans|dress|jacket|coat|shoes|sneakers|boots|sandals|clothing|apparel)\b',
                    r'\b(food|beverage|drink|juice|soda|water|coffee|tea|snack|candy|chocolate|supplement|vitamin)\b',
                    r'\b(furniture|chair|table|bed|sofa|desk|cabinet|shelf|lamp|mirror|curtain|carpet)\b',
                    r'\b(appliance|refrigerator|washing machine|microwave|oven|dishwasher|vacuum|cleaner|air conditioner)\b'
                ],
                'weight': 20
            },
            'year_model': {
                'patterns': [
                    r'\b(20[0-9]{2})\s*(?:model|year|edition|version)?\b',
                    r'\b(?:model|year|edition|version)\s*(20[0-9]{2})\b',
                    r'\b(generation|gen)\s*(\d+)\b',
                    r'\b(\d+)(?:st|nd|rd|th)\s*(?:generation|gen)\b'
                ],
                'weight': 10
            }
        }
        
        # Country and origin information
        self.country_patterns = [
            r'\b(made in|manufactured in|produced in|origin|country of origin|assembled in)\s*([a-z\s]+)\b',
            r'\b(china|usa|japan|germany|korea|taiwan|india|vietnam|thailand|malaysia|singapore|philippines|indonesia|mexico|brazil|italy|france|uk|canada|australia)\b'
        ]
        
        # Packaging information
        self.packaging_patterns = [
            r'\b(pack|box|bottle|can|jar|tube|pouch|bag|container|package|carton|case|unit|piece|set)\b',
            r'\b(\d+)\s*(pack|pieces?|units?|set|boxes?|bottles?|cans?)\b'
        ]
    
    def analyze_description_completeness(self, description: str) -> Dict:
        """Analyze how complete the product description is for customs purposes"""
        
        analysis = {
            'original_description': description,
            'completeness_score': 0,
            'missing_elements': [],
            'found_elements': {},
            'enhancement_needed': True,
            'customs_readiness': 'LOW',
            'recommendations': []
        }
        
        if not description or len(description.strip()) < 5:
            analysis['missing_elements'] = ['Description too short or empty']
            analysis['recommendations'] = ['Provide a detailed product description']
            return analysis
        
        description_lower = description.lower()
        total_possible_score = 0
        achieved_score = 0
        
        # Check each category
        for category, config in self.essential_info_categories.items():
            total_possible_score += config['weight']
            category_found = False
            found_items = []
            
            for pattern in config['patterns']:
                matches = re.findall(pattern, description, re.IGNORECASE)
                if matches:
                    category_found = True
                    found_items.extend(matches)
            
            if category_found:
                achieved_score += config['weight']
                analysis['found_elements'][category] = found_items
            else:
                analysis['missing_elements'].append(category)
        
        # Calculate completeness score
        if total_possible_score > 0:
            analysis['completeness_score'] = (achieved_score / total_possible_score) * 100
        
        # Determine customs readiness
        if analysis['completeness_score'] >= 80:
            analysis['customs_readiness'] = 'HIGH'
            analysis['enhancement_needed'] = False
        elif analysis['completeness_score'] >= 60:
            analysis['customs_readiness'] = 'MEDIUM'
            analysis['enhancement_needed'] = True
        else:
            analysis['customs_readiness'] = 'LOW'
            analysis['enhancement_needed'] = True
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_recommendations(analysis['missing_elements'])
        
        return analysis
    
    def _generate_recommendations(self, missing_elements: List[str]) -> List[str]:
        """Generate recommendations for missing elements"""
        recommendations = []
        
        recommendation_map = {
            'brand': 'Brend nomini qo\'shing (masalan: Apple, Samsung, BMW)',
            'model': 'Model nomini qo\'shing (masalan: iPhone 15, Galaxy S24, X5)',
            'technical_specs': 'Texnik xususiyatlarni qo\'shing (masalan: 256GB, 12MP, 6.7 inch)',
            'physical_attributes': 'Fizik xususiyatlarni qo\'shing (masalan: rang, hajm, og\'irlik)',
            'category_identifiers': 'Mahsulot turini aniqlang (masalan: smartphone, laptop, car)',
            'year_model': 'Ishlab chiqarish yili yoki modelini qo\'shing (masalan: 2024, Gen 5)'
        }
        
        for element in missing_elements:
            if element in recommendation_map:
                recommendations.append(recommendation_map[element])
        
        return recommendations

# ========================= ENHANCED WEB SCRAPER =========================

class CustomsReadyProductScraper:
    """Scraper focused on getting customs-ready product information"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Specialized search strategies for different product types
        self.search_strategies = {
            'electronics': [
                '{product} full specifications technical details',
                '{product} official specs features',
                '{product} complete description model',
                '{product} dimensions weight materials'
            ],
            'automotive': [
                '{product} specifications engine details',
                '{product} model year features',
                '{product} technical specs dimensions',
                '{product} official description'
            ],
            'clothing': [
                '{product} material composition size',
                '{product} brand collection details',
                '{product} fabric specifications',
                '{product} product details'
            ],
            'food_beverage': [
                '{product} ingredients nutritional information',
                '{product} product specifications',
                '{product} brand details packaging',
                '{product} official product information'
            ],
            'general': [
                '{product} full product description',
                '{product} specifications features',
                '{product} complete details',
                '{product} official information'
            ]
        }
    
    def enhance_product_description(self, original_description: str, missing_elements: List[str]) -> Dict:
        """Enhance product description for customs readiness"""
        
        enhancement_result = {
            'original_description': original_description,
            'enhanced_description': original_description,
            'improvements_made': [],
            'additional_specs': {},
            'brand_model_found': {},
            'technical_details': {},
            'physical_attributes': {},
            'sources_used': [],
            'confidence_score': 0,
            'customs_readiness_improved': False
        }
        
        # Determine product category for targeted search
        category = self._determine_product_category(original_description)
        
        # Create targeted search queries
        search_queries = self._create_search_queries(original_description, category, missing_elements)
        
        # Execute searches and collect information
        collected_info = self._execute_searches(search_queries)
        
        # Process and enhance the description
        enhanced_description = self._create_enhanced_description(original_description, collected_info)
        enhancement_result['enhanced_description'] = enhanced_description
        
        # Extract specific information categories
        enhancement_result['brand_model_found'] = self._extract_brand_model(collected_info)
        enhancement_result['technical_details'] = self._extract_technical_details(collected_info)
        enhancement_result['physical_attributes'] = self._extract_physical_attributes(collected_info)
        enhancement_result['additional_specs'] = self._extract_additional_specs(collected_info)
        
        # Track improvements
        enhancement_result['improvements_made'] = self._track_improvements(original_description, enhanced_description)
        enhancement_result['sources_used'] = [source['title'] for source in collected_info.get('sources', [])]
        
        # Calculate confidence score
        enhancement_result['confidence_score'] = self._calculate_confidence_score(collected_info)
        
        # Check if customs readiness improved
        original_score = len(original_description.split())
        enhanced_score = len(enhanced_description.split())
        enhancement_result['customs_readiness_improved'] = enhanced_score > original_score * 1.5
        
        return enhancement_result
    
    def _determine_product_category(self, description: str) -> str:
        """Determine the most likely product category"""
        desc_lower = description.lower()
        
        category_keywords = {
            'electronics': ['phone', 'smartphone', 'laptop', 'computer', 'tablet', 'tv', 'camera', 'headphones', 'watch', 'smartwatch'],
            'automotive': ['car', 'vehicle', 'auto', 'truck', 'motorcycle', 'bike', 'sedan', 'suv', 'bmw', 'mercedes', 'toyota'],
            'clothing': ['shirt', 'pants', 'dress', 'shoes', 'jacket', 'clothing', 'apparel', 'fashion', 'nike', 'adidas'],
            'food_beverage': ['food', 'drink', 'beverage', 'juice', 'water', 'coffee', 'tea', 'snack', 'coca', 'pepsi']
        }
        
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in desc_lower)
            category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'general'
    
    def _create_search_queries(self, description: str, category: str, missing_elements: List[str]) -> List[str]:
        """Create targeted search queries based on missing elements"""
        queries = []
        
        # Base queries from strategy
        base_queries = self.search_strategies.get(category, self.search_strategies['general'])
        for query_template in base_queries:
            queries.append(query_template.format(product=description))
        
        # Targeted queries for missing elements
        if 'brand' in missing_elements:
            queries.append(f"{description} brand manufacturer who makes")
        
        if 'model' in missing_elements:
            queries.append(f"{description} model number version type")
        
        if 'technical_specs' in missing_elements:
            queries.append(f"{description} technical specifications features")
        
        if 'physical_attributes' in missing_elements:
            queries.append(f"{description} dimensions size weight color material")
        
        if 'year_model' in missing_elements:
            queries.append(f"{description} year model when released")
        
        return queries[:6]  # Limit to 6 queries to avoid rate limiting
    
    def _execute_searches(self, queries: List[str]) -> Dict:
        """Execute multiple searches and collect information"""
        collected_info = {
            'raw_text': [],
            'sources': [],
            'structured_data': {}
        }
        
        for query in queries:
            try:
                # Perform Google search
                search_results = self._google_search(query)
                
                # Extract information from top results
                for result in search_results[:2]:  # Top 2 results per query
                    page_info = self._extract_page_information(result['link'])
                    if page_info:
                        collected_info['raw_text'].append(page_info['text'])
                        collected_info['sources'].append({
                            'title': result['title'],
                            'url': result['link']
                        })
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                continue
        
        return collected_info
    
    def _google_search(self, query: str) -> List[Dict]:
        """Perform Google search and return results"""
        try:
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num=5"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                results = []
                
                for result in soup.select('div.g')[:5]:
                    title_elem = result.select_one('h3')
                    link_elem = result.select_one('a')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href')
                        
                        if link and 'http' in link:
                            results.append({
                                'title': title,
                                'link': link
                            })
                
                return results
            
            return []
            
        except Exception:
            return []
    
    def _extract_page_information(self, url: str) -> Optional[Dict]:
        """Extract relevant information from a web page"""
        try:
            response = self.session.get(url, timeout=8)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text()
            
            # Extract structured data
            structured_data = {
                'title': self._extract_title(soup),
                'description': self._extract_description(soup),
                'specifications': self._extract_specifications(soup),
                'features': self._extract_features(soup)
            }
            
            return {
                'text': text_content,
                'structured': structured_data
            }
            
        except Exception:
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_elem = soup.find('title')
        return title_elem.get_text(strip=True) if title_elem else ''
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description"""
        desc_elem = soup.find('meta', {'name': 'description'})
        if desc_elem:
            return desc_elem.get('content', '')
        
        # Try other description sources
        og_desc = soup.find('meta', {'property': 'og:description'})
        if og_desc:
            return og_desc.get('content', '')
        
        return ''
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict:
        """Extract technical specifications"""
        specs = {}
        
        # Look for specification tables
        spec_tables = soup.find_all('table')
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    key = cols[0].get_text(strip=True)
                    value = cols[1].get_text(strip=True)
                    if key and value:
                        specs[key] = value
        
        return specs
    
    def _extract_features(self, soup: BeautifulSoup) -> List[str]:
        """Extract product features"""
        features = []
        
        # Look for feature lists
        feature_lists = soup.find_all(['ul', 'ol'])
        for ul in feature_lists:
            items = ul.find_all('li')
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 10 and len(text) < 100:
                    features.append(text)
        
        return features[:10]  # Limit to 10 features
    
    def _create_enhanced_description(self, original: str, collected_info: Dict) -> str:
        """Create enhanced product description"""
        enhanced = original
        
        # Extract key information from collected text
        all_text = ' '.join(collected_info.get('raw_text', []))
        
        # Extract brand if missing
        brand_match = re.search(r'\b(Apple|Samsung|Huawei|Xiaomi|BMW|Mercedes|Nike|Adidas|Coca Cola|Pepsi|Sony|LG|Dell|HP|Lenovo|Asus|MSI|Canon|Nikon|Bose|JBL|Rolex|Omega|Gucci|Prada|Louis Vuitton|Chanel|Toyota|Honda|Ford|Volkswagen|Audi|Porsche|Jaguar|Volvo|Tesla|Hyundai|Kia|Mazda|Nissan|Lexus|Infiniti|Acura|Cadillac|Chevrolet|Dodge|Jeep|Ram|GMC|Buick|Lincoln|Chrysler|Fiat|Alfa Romeo|Maserati|Ferrari|Lamborghini|Bentley|Rolls Royce|Aston Martin|McLaren|Bugatti|Koenigsegg|Pagani)\b', all_text, re.IGNORECASE)
        if brand_match and brand_match.group(1).lower() not in original.lower():
            enhanced = f"{brand_match.group(1)} {enhanced}"
        
        # Extract model information
        model_patterns = [
            r'\b(iPhone\s+\d+\s*(?:Pro|Max|Plus|Mini|SE)?)\b',
            r'\b(Galaxy\s+[A-Z]+\d+\s*(?:Ultra|Plus|Pro)?)\b',
            r'\b(Pixel\s+\d+\s*(?:Pro|XL)?)\b',
            r'\b(MacBook\s+(?:Air|Pro)\s*\d*)\b',
            r'\b(iPad\s+(?:Pro|Air|Mini)?\s*\d*)\b'
        ]
        
        for pattern in model_patterns:
            model_match = re.search(pattern, all_text, re.IGNORECASE)
            if model_match and model_match.group(1).lower() not in original.lower():
                enhanced = f"{enhanced} {model_match.group(1)}"
                break
        
        # Extract technical specifications
        spec_patterns = [
            r'\b(\d+(?:GB|TB|MB))\b',
            r'\b(\d+\.?\d*(?:inch|"))\b',
            r'\b(\d+MP)\b',
            r'\b(\d+mAh)\b',
            r'\b(4K|8K|HD|Full HD|UHD)\b',
            r'\b(WiFi|Bluetooth|5G|4G|LTE|NFC)\b'
        ]
        
        specs_found = []
        for pattern in spec_patterns:
            spec_matches = re.findall(pattern, all_text, re.IGNORECASE)
            for spec in spec_matches:
                if spec not in enhanced and spec not in specs_found:
                    specs_found.append(spec)
        
        if specs_found:
            enhanced += f" - {', '.join(specs_found[:5])}"
        
        # Extract color information
        color_match = re.search(r'\b(Black|White|Red|Blue|Green|Yellow|Orange|Purple|Pink|Gray|Grey|Silver|Gold|Rose|Space|Midnight|Starlight|Alpine|Sierra|Pacific|Phantom|Mystic|Prism|Aura|Titanium|Ceramic|Leather|Aluminum|Steel|Plastic|Glass|Carbon|Fiber)\b', all_text, re.IGNORECASE)
        if color_match and color_match.group(1).lower() not in original.lower():
            enhanced += f" - {color_match.group(1)}"
        
        # Extract year information
        year_match = re.search(r'\b(20[0-9]{2})\b', all_text)
        if year_match and year_match.group(1) not in original:
            enhanced += f" ({year_match.group(1)} model)"
        
        # Clean up the enhanced description
        enhanced = re.sub(r'\s+', ' ', enhanced).strip()
        
        return enhanced
    
    def _extract_brand_model(self, collected_info: Dict) -> Dict:
        """Extract brand and model information"""
        all_text = ' '.join(collected_info.get('raw_text', []))
        
        brand_model = {
            'brand': '',
            'model': '',
            'series': ''
        }
        
        # Extract brand
        brand_match = re.search(r'\b(Apple|Samsung|Huawei|Xiaomi|BMW|Mercedes|Nike|Adidas|Coca Cola|Pepsi|Sony|LG|Dell|HP|Lenovo|Asus)\b', all_text, re.IGNORECASE)
        if brand_match:
            brand_model['brand'] = brand_match.group(1)
        
        # Extract model
        model_patterns = [
            r'\b(iPhone\s+\d+\s*(?:Pro|Max|Plus|Mini|SE)?)\b',
            r'\b(Galaxy\s+[A-Z]+\d+\s*(?:Ultra|Plus|Pro)?)\b',
            r'\b(Pixel\s+\d+\s*(?:Pro|XL)?)\b'
        ]
        
        for pattern in model_patterns:
            model_match = re.search(pattern, all_text, re.IGNORECASE)
            if model_match:
                brand_model['model'] = model_match.group(1)
                break
        
        return brand_model
    
    def _extract_technical_details(self, collected_info: Dict) -> Dict:
        """Extract technical details"""
        all_text = ' '.join(collected_info.get('raw_text', []))
        
        tech_details = {
            'memory': [],
            'display': [],
            'camera': [],
            'battery': [],
            'connectivity': [],
            'processor': []
        }
        
        # Memory
        memory_matches = re.findall(r'\b(\d+(?:GB|TB|MB))\b', all_text, re.IGNORECASE)
        tech_details['memory'] = list(set(memory_matches))
        
        # Display
        display_matches = re.findall(r'\b(\d+\.?\d*(?:inch|"))\b', all_text, re.IGNORECASE)
        tech_details['display'] = list(set(display_matches))
        
        # Camera
        camera_matches = re.findall(r'\b(\d+MP)\b', all_text, re.IGNORECASE)
        tech_details['camera'] = list(set(camera_matches))
        
        # Battery
        battery_matches = re.findall(r'\b(\d+mAh)\b', all_text, re.IGNORECASE)
        tech_details['battery'] = list(set(battery_matches))
        
        # Connectivity
        connectivity_matches = re.findall(r'\b(WiFi|Bluetooth|5G|4G|LTE|NFC|USB|HDMI|Ethernet)\b', all_text, re.IGNORECASE)
        tech_details['connectivity'] = list(set(connectivity_matches))
        
        return tech_details
    
    def _extract_physical_attributes(self, collected_info: Dict) -> Dict:
        """Extract physical attributes"""
        all_text = ' '.join(collected_info.get('raw_text', []))
        
        attributes = {
            'color': [],
            'material': [],
            'dimensions': [],
            'weight': []
        }
        
        # Color
        color_matches = re.findall(r'\b(Black|White|Red|Blue|Green|Yellow|Orange|Purple|Pink|Gray|Grey|Silver|Gold|Rose|Space|Midnight|Starlight|Alpine|Sierra|Pacific|Phantom|Mystic|Prism|Aura|Titanium|Ceramic)\b', all_text, re.IGNORECASE)
        attributes['color'] = list(set(color_matches))
        
        # Material
        material_matches = re.findall(r'\b(Aluminum|Steel|Plastic|Glass|Carbon|Fiber|Leather|Silicone|Rubber|Wood|Metal|Ceramic|Titanium)\b', all_text, re.IGNORECASE)
        attributes['material'] = list(set(material_matches))
        
        # Dimensions
        dimension_matches = re.findall(r'\b(\d+\.?\d*\s*(?:mm|cm|inch|"))\b', all_text, re.IGNORECASE)
        attributes['dimensions'] = list(set(dimension_matches))
        
        # Weight
        weight_matches = re.findall(r'\b(\d+\.?\d*\s*(?:g|kg|lbs|oz))\b', all_text, re.IGNORECASE)
        attributes['weight'] = list(set(weight_matches))
        
        return attributes
    
    def _extract_additional_specs(self, collected_info: Dict) -> Dict:
        """Extract additional specifications"""
        all_text = ' '.join(collected_info.get('raw_text', []))
        
        specs = {
            'operating_system': [],
            'year': [],
            'special_features': [],
            'country_origin': []
        }
        
        # Operating System
        os_matches = re.findall(r'\b(Android|iOS|Windows|macOS|Linux|Chrome OS)\s*(\d+\.?\d*)?\b', all_text, re.IGNORECASE)
        specs['operating_system'] = [f"{match[0]} {match[1]}" if match[1] else match[0] for match in os_matches]
        
        # Year
        year_matches = re.findall(r'\b(20[0-9]{2})\b', all_text)
        specs['year'] = list(set(year_matches))
        
        # Special Features
        feature_matches = re.findall(r'\b(Waterproof|Wireless|Fast Charging|Face ID|Touch ID|Fingerprint|Dual SIM|Triple Camera|Quad Camera|AI|Smart|Pro|Max|Ultra|Premium|Limited Edition)\b', all_text, re.IGNORECASE)
        specs['special_features'] = list(set(feature_matches))
        
        # Country of Origin
        country_matches = re.findall(r'\b(?:Made in|Manufactured in|Origin|Country of origin|Assembled in)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', all_text, re.IGNORECASE)
        specs['country_origin'] = list(set([match for match in country_matches]))
        
        return specs
    
    def _track_improvements(self, original: str, enhanced: str) -> List[str]:
        """Track what improvements were made"""
        improvements = []
        
        if len(enhanced) > len(original) * 1.2:
            improvements.append("Tavsif uzaytirildi")
        
        if any(brand in enhanced.lower() for brand in ['apple', 'samsung', 'bmw', 'mercedes', 'nike', 'adidas']):
            improvements.append("Brend qo'shildi")
        
        if any(spec in enhanced.lower() for spec in ['gb', 'tb', 'inch', 'mp', 'mah']):
            improvements.append("Texnik xususiyatlar qo'shildi")
        
        if any(color in enhanced.lower() for color in ['black', 'white', 'red', 'blue', 'silver', 'gold']):
            improvements.append("Rang ma'lumoti qo'shildi")
        
        if re.search(r'\b20[0-9]{2}\b', enhanced):
            improvements.append("Yil ma'lumoti qo'shildi")
        
        return improvements
    
    def _calculate_confidence_score(self, collected_info: Dict) -> float:
        """Calculate confidence score for the enhancement"""
        score = 0
        
        # Base score for having sources
        sources_count = len(collected_info.get('sources', []))
        score += min(sources_count * 15, 60)
        
        # Score for text content
        text_length = len(' '.join(collected_info.get('raw_text', [])))
        if text_length > 1000:
            score += 20
        elif text_length > 500:
            score += 15
        elif text_length > 200:
            score += 10
        
        # Score for structured data
        structured_data = collected_info.get('structured_data', {})
        if structured_data:
            score += 20
        
        return min(score, 100)

# ========================= MAIN FUNCTIONS =========================

def validate_uploaded_file(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate uploaded file structure"""
    required_columns = ['ID', 'Tovar_nomi']
    
    if not all(col in df.columns for col in required_columns):
        return False, "Faylda 'ID' va 'Tovar_nomi' ustunlari mavjud emas"
    
    if df.empty:
        return False, "Fayl bo'sh"
    
    if df['ID'].duplicated().any():
        return False, "ID ustunida takrorlanuvchi qiymatlar mavjud"
    
    empty_descriptions = df['Tovar_nomi'].isna().sum()
    if empty_descriptions > 0:
        return False, f"{empty_descriptions} ta bo'sh tovar tavsifi mavjud"
    
    return True, "Fayl tuzilishi to'g'ri"

def process_products_for_customs(df: pd.DataFrame, enhancer: ProductDescriptionEnhancer, scraper: CustomsReadyProductScraper) -> pd.DataFrame:
    """Process products to make them customs-ready"""
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_products = len(df)
    
    for idx, row in df.iterrows():
        # Update progress
        progress = (idx + 1) / total_products
        progress_bar.progress(progress)
        status_text.text(f"Tahlil qilinmoqda: {idx + 1}/{total_products} - {row['Tovar_nomi']}")
        
        # Analyze original description
        analysis = enhancer.analyze_description_completeness(row['Tovar_nomi'])
        
        # Create result row
        result_row = {
            'ID': row['ID'],
            'Asl_tavsif': row['Tovar_nomi'],
            'Dastlabki_toliqlik': f"{analysis['completeness_score']:.1f}%",
            'Bojxona_tayyorligi': analysis['customs_readiness'],
            'Topilgan_elementlar': ', '.join(analysis['found_elements'].keys()),
            'Yetishmayotgan_elementlar': ', '.join(analysis['missing_elements']),
            'Toldirilgan_tavsif': row['Tovar_nomi'],
            'Qoshimcha_malumotlar': '',
            'Yakuniy_toliqlik': f"{analysis['completeness_score']:.1f}%",
            'Yakuniy_tayyorlik': analysis['customs_readiness'],
            'Scraping_manbalar': 0,
            'Ishonch_darajasi': '0%',
            'Tavsiyalar': '; '.join(analysis['recommendations'][:3])
        }
        
        # If enhancement needed, use scraper
        if analysis['enhancement_needed']:
            try:
                enhancement_result = scraper.enhance_product_description(row['Tovar_nomi'], analysis['missing_elements'])
                
                # Update with enhanced information
                result_row['Toldirilgan_tavsif'] = enhancement_result['enhanced_description']
                result_row['Qoshimcha_malumotlar'] = '; '.join(enhancement_result['improvements_made'])
                result_row['Scraping_manbalar'] = len(enhancement_result['sources_used'])
                result_row['Ishonch_darajasi'] = f"{enhancement_result['confidence_score']:.1f}%"
                
                # Re-analyze enhanced description
                enhanced_analysis = enhancer.analyze_description_completeness(enhancement_result['enhanced_description'])
                result_row['Yakuniy_toliqlik'] = f"{enhanced_analysis['completeness_score']:.1f}%"
                result_row['Yakuniy_tayyorlik'] = enhanced_analysis['customs_readiness']
                
                # Add technical details if found
                if enhancement_result['technical_details']:
                    tech_summary = []
                    for key, values in enhancement_result['technical_details'].items():
                        if values:
                            tech_summary.append(f"{key}: {', '.join(values[:2])}")
                    
                    if tech_summary:
                        result_row['Qoshimcha_malumotlar'] += f" | Texnik: {'; '.join(tech_summary[:3])}"
                
            except Exception as e:
                result_row['Qoshimcha_malumotlar'] = f"Scraping xatoligi: {str(e)}"
        
        results.append(result_row)
        
        # Rate limiting
        time.sleep(0.5)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(results)

# ========================= MAIN APPLICATION =========================

def main():
    # Header
    st.markdown('<h1 class="main-header">📝 BOJXONA UCHUN TOVAR TAVSIFI TO\'LDIRISH</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Tovar tavsiflarini bojxona xodimlari HS kodini oson aniqlay oladigan darajada to\'ldirish</p>', unsafe_allow_html=True)
    
    # Check NLTK status
    if not nltk_ready:
        st.error("⚠️ NLTK kutubxonasi to'liq yuklanmadi. Loyiha oddiy rejimda ishlaydi.")
        with st.expander("🔧 NLTK o'rnatish yo'riqnomasi"):
            st.code("""
# Terminal'da quyidagi buyruqlarni bajaring:
pip install nltk

# Yoki requirements.txt orqali:
pip install -r requirements.txt

# NLTK ma'lumotlarini yuklab olish:
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
            """)
    else:
        st.success("✅ NLTK kutubxonasi muvaffaqiyatli yuklandi!")
    
    # Information box
    st.markdown("""
    <div class="highlight-box">
        <h3>🎯 Loyiha maqsadi</h3>
        <p><strong>Muammo:</strong> Noto'liq tovar tavsifi → Bojxona xodimi HS kodini aniqlay olmaydi</p>
        <p><strong>Yechim:</strong> NLP tahlil + Web scraping → To'liq va aniq tovar tavsifi</p>
        <p><strong>Natija:</strong> Bojxona xodimi HS kodini osongina aniqlay oladi</p>
        <br>
        <p><strong>Tavsifda bo'lishi kerak:</strong> Brend, Model, Texnik xususiyatlar, Rang, Hajm, Material, Yil</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Sozlamalar")
        
        # NLTK status
        if nltk_ready:
            st.success("🧠 NLTK: Faol")
        else:
            st.error("🧠 NLTK: Nofaol")
            st.info("Oddiy rejimda ishlaydi")
        
        enable_analysis = st.checkbox("NLP tahlil yoqish", value=True)
        enable_scraping = st.checkbox("Web scraping yoqish", value=True)
        
        st.markdown("### 🎯 To'liqlik darajasi")
        completeness_threshold = st.slider("Minimal to'liqlik (%)", 60, 90, 75)
        
        st.markdown("### 📊 Bojxona tayyorligi")
        st.info("""
        **HIGH (80%+):** Bojxona tayyor  
        **MEDIUM (60-80%):** Qo'shimcha ma'lumot kerak  
        **LOW (<60%):** Scraping zarur
        """)
        
        st.markdown("### 🔍 Tavsif elementlari")
        required_elements = [
            "✅ Brend (Apple, Samsung, BMW)",
            "✅ Model (iPhone 15, Galaxy S24)",
            "✅ Texnik xususiyatlar (256GB, 12MP)",
            "✅ Fizik xususiyatlar (Black, Titanium)",
            "✅ Kategoriya (Smartphone, Laptop)",
            "✅ Yil (2024 model)"
        ]
        
        for element in required_elements:
            st.markdown(f"• {element}")
        
        # NLP Information
        st.markdown("### 🧠 NLP haqida")
        st.info("""
        **NLTK** - Natural Language Toolkit
        
        **Vazifalar:**
        • Matnni tahlil qilish
        • So'zlarni ajratish  
        • Lemmatization
        • Stop words filtri
        """)
        
        if not nltk_ready:
            st.markdown("### 🔧 NLTK o'rnatish")
            st.code("pip install nltk")
            st.code("python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')\"")
        
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Fayl yuklash", "📊 Tahlil natijalari", "🎯 Bojxona tayyorligi", "🧪 Test"])
    
    with tab1:
        st.markdown("### 📁 Excel/CSV fayl yuklash")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Faylni yuklang (ID va Tovar_nomi ustunlari bilan)",
            type=['xlsx', 'xls', 'csv'],
            help="Fayl namunasi: ID | Tovar_nomi"
        )
        
        if uploaded_file:
            try:
                # Read file
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Validate file
                is_valid, validation_message = validate_uploaded_file(df)
                
                if is_valid:
                    st.success(f"✅ {validation_message}")
                    
                    # Display file statistics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df)}</div><div class="metric-label">Jami tovarlar</div></div>', unsafe_allow_html=True)
                    
                    with col2:
                        avg_length = df['Tovar_nomi'].str.len().mean()
                        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_length:.1f}</div><div class="metric-label">O\'rtacha uzunlik</div></div>', unsafe_allow_html=True)
                    
                    with col3:
                        unique_products = df['Tovar_nomi'].nunique()
                        st.markdown(f'<div class="metric-card"><div class="metric-value">{unique_products}</div><div class="metric-label">Noyob tovarlar</div></div>', unsafe_allow_html=True)
                    
                    with col4:
                        # Quick completeness check
                        enhancer = ProductDescriptionEnhancer()
                        quick_analysis = [enhancer.analyze_description_completeness(desc) for desc in df['Tovar_nomi'].head(10)]
                        avg_completeness = sum(a['completeness_score'] for a in quick_analysis) / len(quick_analysis)
                        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_completeness:.1f}%</div><div class="metric-label">O\'rtacha to\'liqlik</div></div>', unsafe_allow_html=True)
                    
                    # Display sample data
                    st.markdown("### 📋 Fayl namunasi")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # Quick analysis preview
                    st.markdown("### 🔍 Tezkor tahlil (birinchi 5 ta tovar)")
                    
                    preview_results = []
                    for idx, row in df.head(5).iterrows():
                        analysis = enhancer.analyze_description_completeness(row['Tovar_nomi'])
                        preview_results.append({
                            'ID': row['ID'],
                            'Tovar_nomi': row['Tovar_nomi'],
                            'To\'liqlik': f"{analysis['completeness_score']:.1f}%",
                            'Tayyorlik': analysis['customs_readiness'],
                            'Yetishmayotgan': ', '.join(analysis['missing_elements'][:3])
                        })
                    
                    preview_df = pd.DataFrame(preview_results)
                    st.dataframe(preview_df, use_container_width=True)
                    
                    # Process button
                    st.markdown("### 🚀 To'liq tahlil va to'ldirish")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f'<div class="analysis-card">📊 {len(df)} ta tovar tahlil qilinadi va to\'ldiriladi</div>', unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("🔍 Boshlash", type="primary"):
                            if enable_analysis:
                                # Initialize components
                                enhancer = ProductDescriptionEnhancer()
                                scraper = CustomsReadyProductScraper()
                                
                                # Process products
                                with st.spinner("Tovarlar tahlil qilinmoqda va to'ldirilmoqda..."):
                                    results_df = process_products_for_customs(df, enhancer, scraper)
                                    
                                    # Save to session state
                                    st.session_state.results = results_df
                                    st.session_state.original_df = df
                                
                                st.success("✅ Tahlil va to'ldirish tugallandi!")
                                st.balloons()
                            else:
                                st.error("NLP tahlil sozlamalarda yoqilmagan")
                
                else:
                    st.error(f"❌ {validation_message}")
                    
                    # Show sample file format
                    st.markdown("### 📋 To'g'ri fayl formati")
                    sample_data = {
                        'ID': [1, 2, 3, 4, 5],
                        'Tovar_nomi': [
                            'iPhone',
                            'Samsung Galaxy',
                            'MacBook Pro',
                            'BMW X5',
                            'Nike Air Max'
                        ]
                    }
                    sample_df = pd.DataFrame(sample_data)
                    st.dataframe(sample_df, use_container_width=True)
                    
                    # Download sample file
                    sample_excel = io.BytesIO()
                    with pd.ExcelWriter(sample_excel, engine='openpyxl') as writer:
                        sample_df.to_excel(writer, index=False, sheet_name='Sample')
                    sample_excel.seek(0)
                    
                    st.download_button(
                        label="📥 Namuna fayl yuklab olish",
                        data=sample_excel.getvalue(),
                        file_name="sample_file.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
            except Exception as e:
                st.error(f"❌ Fayl o'qishda xatolik: {str(e)}")
    
    with tab2:
        st.markdown("### 📊 Tahlil natijalari")
        
        if 'results' in st.session_state:
            results_df = st.session_state.results
            
            # Summary statistics
            st.markdown("### 📈 Umumiy statistika")
            
            total_products = len(results_df)
            high_readiness = len(results_df[results_df['Yakuniy_tayyorlik'] == 'HIGH'])
            medium_readiness = len(results_df[results_df['Yakuniy_tayyorlik'] == 'MEDIUM'])
            low_readiness = len(results_df[results_df['Yakuniy_tayyorlik'] == 'LOW'])
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{total_products}</div><div class="metric-label">Jami tovarlar</div></div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #28a745;">{high_readiness}</div><div class="metric-label">Yuqori tayyorlik</div></div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #ffc107;">{medium_readiness}</div><div class="metric-label">O\'rta tayyorlik</div></div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #dc3545;">{low_readiness}</div><div class="metric-label">Past tayyorlik</div></div>', unsafe_allow_html=True)
            
            # Readiness distribution
            st.markdown("### 🎯 Bojxona tayyorligi taqsimoti")
            
            readiness_data = {
                'Tayyorlik darajasi': ['HIGH', 'MEDIUM', 'LOW'],
                'Miqdor': [high_readiness, medium_readiness, low_readiness],
                'Foiz': [f"{(high_readiness/total_products)*100:.1f}%", f"{(medium_readiness/total_products)*100:.1f}%", f"{(low_readiness/total_products)*100:.1f}%"]
            }
            
            for i, (level, count, percentage) in enumerate(zip(readiness_data['Tayyorlik darajasi'], readiness_data['Miqdor'], readiness_data['Foiz'])):
                if level == 'HIGH':
                    st.markdown(f'<div class="completeness-high">✅ {level}: {count} ta tovar ({percentage})</div>', unsafe_allow_html=True)
                elif level == 'MEDIUM':
                    st.markdown(f'<div class="completeness-medium">⚠️ {level}: {count} ta tovar ({percentage})</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="completeness-low">❌ {level}: {count} ta tovar ({percentage})</div>', unsafe_allow_html=True)
            
            # Improvement analysis
            st.markdown("### 📈 Takomillashtirish tahlili")
            
            # Parse completeness scores
            initial_scores = results_df['Dastlabki_toliqlik'].str.replace('%', '').astype(float)
            final_scores = results_df['Yakuniy_toliqlik'].str.replace('%', '').astype(float)
            
            improved_count = len(final_scores[final_scores > initial_scores])
            avg_improvement = (final_scores - initial_scores).mean()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f'<div class="enhancement-card">🔄 Takomillashtirilgan: {improved_count} ta tovar</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown(f'<div class="enhancement-card">📊 O\'rtacha yaxshilanish: {avg_improvement:.1f}%</div>', unsafe_allow_html=True)
            
            # Display results table
            st.markdown("### 📋 Batafsil natijalar")
            st.dataframe(results_df, use_container_width=True)
            
        else:
            st.info("📤 Hozircha tahlil natijalari yo'q. Avval fayl yuklang va tahlil qiling.")
    
    with tab3:
        st.markdown("### 🎯 Bojxona tayyorligi hisoboti")
        
        if 'results' in st.session_state:
            results_df = st.session_state.results
            
            # Export functionality
            st.markdown("### 📥 Natijalarni eksport qilish")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                # Create comprehensive Excel report
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Main results
                    results_df.to_excel(writer, index=False, sheet_name='Asosiy_natijalar')
                    
                    # Summary statistics
                    summary_data = {
                        'Metrika': [
                            'Jami tovarlar',
                            'Yuqori tayyorlik (HIGH)',
                            'O\'rta tayyorlik (MEDIUM)',
                            'Past tayyorlik (LOW)',
                            'Takomillashtirilgan tovarlar',
                            'O\'rtacha dastlabki to\'liqlik',
                            'O\'rtacha yakuniy to\'liqlik',
                            'O\'rtacha yaxshilanish'
                        ],
                        'Qiymat': [
                            len(results_df),
                            len(results_df[results_df['Yakuniy_tayyorlik'] == 'HIGH']),
                            len(results_df[results_df['Yakuniy_tayyorlik'] == 'MEDIUM']),
                            len(results_df[results_df['Yakuniy_tayyorlik'] == 'LOW']),
                            len(results_df[results_df['Yakuniy_toliqlik'].str.replace('%', '').astype(float) > results_df['Dastlabki_toliqlik'].str.replace('%', '').astype(float)]),
                            f"{results_df['Dastlabki_toliqlik'].str.replace('%', '').astype(float).mean():.1f}%",
                            f"{results_df['Yakuniy_toliqlik'].str.replace('%', '').astype(float).mean():.1f}%",
                            f"{(results_df['Yakuniy_toliqlik'].str.replace('%', '').astype(float) - results_df['Dastlabki_toliqlik'].str.replace('%', '').astype(float)).mean():.1f}%"
                        ]
                    }
                    
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, index=False, sheet_name='Xulosa')
                    
                    # High readiness products (ready for customs)
                    high_readiness_df = results_df[results_df['Yakuniy_tayyorlik'] == 'HIGH']
                    high_readiness_df.to_excel(writer, index=False, sheet_name='Bojxona_tayyor')
                    
                    # Products needing more work
                    needs_work_df = results_df[results_df['Yakuniy_tayyorlik'] == 'LOW']
                    needs_work_df.to_excel(writer, index=False, sheet_name='Qoshimcha_ish_kerak')
                
                output.seek(0)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"bojxona_tayyorligi_{timestamp}.xlsx"
                
                st.download_button(
                    label="📥 To'liq hisobotni yuklab olish",
                    data=output.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            
            # Top improved products
            st.markdown("### 🏆 Eng ko'p takomillashtirilgan tovarlar")
            
            # Calculate improvement for each product
            results_df['Yaxshilanish'] = results_df['Yakuniy_toliqlik'].str.replace('%', '').astype(float) - results_df['Dastlabki_toliqlik'].str.replace('%', '').astype(float)
            
            top_improved = results_df.nlargest(10, 'Yaxshilanish')[['ID', 'Asl_tavsif', 'Toldirilgan_tavsif', 'Yaxshilanish', 'Yakuniy_tayyorlik']]
            
            if len(top_improved) > 0:
                st.dataframe(top_improved, use_container_width=True)
            else:
                st.info("Takomillashtirilgan tovarlar yo'q")
            
            # Clear results
            if st.button("🗑️ Barcha natijalarni tozalash"):
                if 'results' in st.session_state:
                    del st.session_state.results
                if 'original_df' in st.session_state:
                    del st.session_state.original_df
                st.rerun()
                
        else:
            st.info("📊 Hisobot uchun avval faylni tahlil qiling")
    
    with tab4:
        st.markdown("### 🧪 Bitta tovar testi")
        
        # Single product test
        col1, col2 = st.columns([3, 1])
        
        with col1:
            test_product = st.text_input(
                "Test tovar tavsifi:",
                placeholder="Masalan: iPhone yoki Samsung Galaxy yoki BMW X5",
                value=""
            )
        
        with col2:
            if st.button("🔍 Tahlil qilish", type="primary"):
                if test_product:
                    # Initialize enhancer
                    enhancer = ProductDescriptionEnhancer()
                    scraper = CustomsReadyProductScraper()
                    
                    # Analyze original
                    with st.spinner("Dastlabki tahlil..."):
                        original_analysis = enhancer.analyze_description_completeness(test_product)
                    
                    # Display original analysis
                    st.markdown("#### 📊 Dastlabki tahlil")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("To'liqlik darajasi", f"{original_analysis['completeness_score']:.1f}%")
                    
                    with col2:
                        st.metric("Bojxona tayyorligi", original_analysis['customs_readiness'])
                    
                    with col3:
                        st.metric("Takomillashtirish kerakmi", "Ha" if original_analysis['enhancement_needed'] else "Yo'q")
                    
                    # Show found and missing elements
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**✅ Topilgan elementlar:**")
                        if original_analysis['found_elements']:
                            for element, items in original_analysis['found_elements'].items():
                                st.markdown(f"• {element}: {', '.join(str(item) for item in items[:3])}")
                        else:
                            st.markdown("• Hech narsa topilmadi")
                    
                    with col2:
                        st.markdown("**❌ Yetishmayotgan elementlar:**")
                        if original_analysis['missing_elements']:
                            for element in original_analysis['missing_elements']:
                                st.markdown(f"• {element}")
                        else:
                            st.markdown("• Hamma narsa mavjud")
                    
                    # Show recommendations
                    if original_analysis['recommendations']:
                        st.markdown("**💡 Tavsiyalar:**")
                        for rec in original_analysis['recommendations']:
                            st.markdown(f"• {rec}")
                    
                    # If enhancement needed, perform scraping
                    if original_analysis['enhancement_needed']:
                        st.markdown("#### 🔍 Takomillashtirish (Web Scraping)")
                        
                        with st.spinner("Google'dan qo'shimcha ma'lumot olinmoqda..."):
                            enhancement_result = scraper.enhance_product_description(test_product, original_analysis['missing_elements'])
                        
                        if enhancement_result['enhanced_description'] != test_product:
                            st.success("✅ Takomillashtirish muvaffaqiyatli!")
                            
                            # Show before and after
                            st.markdown("**📝 Tavsif taqqoslash:**")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Asl tavsif:**")
                                st.info(test_product)
                            
                            with col2:
                                st.markdown("**Takomillashtirilgan tavsif:**")
                                st.success(enhancement_result['enhanced_description'])
                            
                            # Show improvements
                            if enhancement_result['improvements_made']:
                                st.markdown("**🔄 Qilingan yaxshilanishlar:**")
                                for improvement in enhancement_result['improvements_made']:
                                    st.markdown(f"• {improvement}")
                            
                            # Show technical details
                            if enhancement_result['technical_details']:
                                st.markdown("**⚙️ Topilgan texnik xususiyatlar:**")
                                for category, details in enhancement_result['technical_details'].items():
                                    if details:
                                        st.markdown(f"• {category}: {', '.join(details[:3])}")
                            
                            # Show sources
                            if enhancement_result['sources_used']:
                                st.markdown("**📚 Foydalanilgan manbalar:**")
                                for source in enhancement_result['sources_used'][:3]:
                                    st.markdown(f'<div class="source-card">🔗 {source}</div>', unsafe_allow_html=True)
                            
                            # Re-analyze enhanced description
                            enhanced_analysis = enhancer.analyze_description_completeness(enhancement_result['enhanced_description'])
                            
                            st.markdown("#### 📈 Yakuniy natija")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                improvement = enhanced_analysis['completeness_score'] - original_analysis['completeness_score']
                                st.metric("To'liqlik yaxshilanishi", f"+{improvement:.1f}%")
                            
                            with col2:
                                st.metric("Yangi bojxona tayyorligi", enhanced_analysis['customs_readiness'])
                            
                            with col3:
                                st.metric("Scraping ishonch darajasi", f"{enhancement_result['confidence_score']:.1f}%")
                            
                        else:
                            st.warning("⚠️ Qo'shimcha ma'lumot topilmadi")
                            
                    else:
                        st.success("🎉 Tavsif allaqachon bojxona uchun tayyor!")
                        
                else:
                    st.warning("Test uchun tovar tavsifini kiriting")
        
        # Example products for testing
        st.markdown("### 🎯 Test misollari")
        
        examples = [
            ("iPhone", "Noto'liq tavsif - brend bor, model yo'q"),
            ("Samsung Galaxy S24 Ultra 512GB", "Yaxshi tavsif - brend, model, hajm bor"),
            ("BMW X5 xDrive40i 2024 Black", "To'liq tavsif - bojxona tayyor"),
            ("Coca Cola", "Noto'liq tavsif - faqat brend"),
            ("MacBook Pro M3 16 inch", "Yaxshi tavsif - texnik xususiyatlar bor"),
            ("Nike Air Max 270", "O'rtacha tavsif - brend va model bor"),
            ("Sony WH-1000XM5", "Yaxshi tavsif - brend va model bor"),
            ("Tesla Model 3", "O'rtacha tavsif - brend va model bor")
        ]
        
        col1, col2 = st.columns(2)
        
        for i, (example, description) in enumerate(examples):
            with col1 if i % 2 == 0 else col2:
                if st.button(f"🧪 {example}", key=f"example_{i}"):
                    st.session_state.test_product = example
                    st.rerun()
                
                st.caption(description)

if __name__ == "__main__":
    main()