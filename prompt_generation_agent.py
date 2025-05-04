import logging
import random

logger = logging.getLogger(__name__)

class PromptGenerationAgent:
    def __init__(self):
        """初始化提示词生成代理"""
        self.character_traits = {
            'gender': ['boy', 'girl'],
            'species': [
                # 人类角色
                'princess', 'prince', 'knight', 'wizard', 'fairy', 'mermaid', 'pirate', 'ninja', 'robot', 'alien',
                # 动物角色
                'puppy', 'kitten', 'bunny', 'bear cub', 'baby dragon', 'baby unicorn', 'baby phoenix', 'baby griffin',
                # 幻想生物
                'baby monster', 'baby yeti', 'baby sasquatch', 'baby dragon', 'baby phoenix'
            ],
            'hair_style': [
                'long flowing hair', 'short spiky hair', 'curly pigtails', 'braided hair', 'messy hair',
                'wavy hair', 'straight hair', 'bob cut', 'pixie cut', 'ponytail'
            ],
            'clothing': [
                'princess dress', 'knight armor', 'wizard robe', 'pirate costume', 'ninja suit',
                'fairy wings', 'mermaid tail', 'robot suit', 'space suit', 'magical cape',
                'casual t-shirt', 'school uniform', 'party dress', 'sports uniform', 'rainbow outfit'
            ],
            'accessories': [
                'crown', 'magic wand', 'sword', 'shield', 'backpack', 'glasses',
                'hat', 'bow', 'ribbon', 'necklace', 'bracelet', 'toy',
                'wings', 'tail', 'horns', 'antenna', 'robot parts'
            ]
        }
        
        self.default_character = {
            'gender': 'child',
            'species': 'princess',
            'hair_style': 'long flowing hair',
            'clothing': 'princess dress',
            'accessories': 'crown'
        }

    def analyze_character(self, analysis):
        """分析图片中的角色特征"""
        character = {}
        
        # 根据亮度推断角色情绪和类型
        if analysis['brightness'] > 0.7:
            character['mood'] = 'cheerful and bright'
            # 明亮场景适合的角色
            character['species'] = random.choice(['princess', 'fairy', 'baby unicorn', 'baby phoenix'])
        elif analysis['brightness'] < 0.3:
            character['mood'] = 'mysterious and dreamy'
            # 暗场景适合的角色
            character['species'] = random.choice(['wizard', 'ninja', 'baby dragon', 'baby monster'])
        else:
            character['mood'] = 'gentle and calm'
            # 中性场景适合的角色
            character['species'] = random.choice(['prince', 'knight', 'puppy', 'kitten'])
            
        # 根据对比度推断风格和装扮
        if analysis['contrast'] > 0.7:
            character['style'] = 'bold and vibrant'
            # 高对比度适合的装扮
            character['clothing'] = random.choice(['knight armor', 'pirate costume', 'robot suit'])
        elif analysis['contrast'] < 0.3:
            character['style'] = 'soft and gentle'
            # 低对比度适合的装扮
            character['clothing'] = random.choice(['princess dress', 'fairy wings', 'wizard robe'])
        else:
            character['style'] = 'balanced and natural'
            # 中等对比度适合的装扮
            character['clothing'] = random.choice(['casual t-shirt', 'school uniform', 'party dress'])
            
        # 根据边缘密度推断细节程度和配饰
        if analysis['edges']['edge_density'] > 0.7:
            character['detail_level'] = 'detailed and intricate'
            # 高细节适合的配饰
            character['accessories'] = random.choice(['crown', 'magic wand', 'sword', 'shield'])
        elif analysis['edges']['edge_density'] < 0.3:
            character['detail_level'] = 'simple and clean'
            # 低细节适合的配饰
            character['accessories'] = random.choice(['bow', 'ribbon', 'simple hat'])
        else:
            character['detail_level'] = 'moderately detailed'
            # 中等细节适合的配饰
            character['accessories'] = random.choice(['backpack', 'glasses', 'necklace'])
            
        return character
    
    def generate_character_prompt(self, character_analysis):
        """生成角色描述提示词"""
        # 基础角色特征
        base_traits = [
            "cute child character",
            "innocent expression",
            "big expressive eyes",
            "soft features",
            "playful pose"
        ]
        
        # 添加分析得到的特征
        if 'mood' in character_analysis:
            base_traits.append(character_analysis['mood'])
        if 'style' in character_analysis:
            base_traits.append(character_analysis['style'])
        if 'detail_level' in character_analysis:
            base_traits.append(character_analysis['detail_level'])
            
        # 添加角色特征
        for trait_type in ['species', 'hair_style', 'clothing', 'accessories']:
            if trait_type in character_analysis:
                base_traits.append(character_analysis[trait_type])
            else:
                # 如果没有分析到该特征，从特征库中随机选择
                trait = random.choice(self.character_traits[trait_type])
                base_traits.append(trait)
                
        return ", ".join(base_traits)
    
    def generate_prompts(self, analysis):
        """
        根据图片分析结果生成提示词
        
        Args:
            analysis (dict): 图片分析结果
            
        Returns:
            dict: 包含各种提示词的字典
        """
        try:
            # 分析角色特征
            character_analysis = self.analyze_character(analysis)
            character_prompt = self.generate_character_prompt(character_analysis)
            
            # 生成增强提示词
            enhancement_prompt = f"{character_prompt}, children's book illustration style, bright colors, clean lines, simple background, sticker style, white background, no text, no watermark, high quality"
            
            # 生成动画提示词
            animation_prompt = f"{character_prompt}, gentle movement, playful animation, smooth transition, children's animation style, bright colors, simple background"
            
            # 生成负面提示词
            negative_prompt = "bad hands, text, watermark, low quality, blurry, malformed, abnormal, adult content, complex details, realistic style, dark colors, busy background"
            
            return {
                "enhancement_prompt": enhancement_prompt,
                "animation_prompt": animation_prompt,
                "negative_prompt": negative_prompt
            }
            
        except Exception as e:
            logger.error(f"提示词生成失败: {str(e)}")
            raise 