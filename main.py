import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.font_manager as fm
from PIL import Image
from IPython.display import display, FileLink, Image as IPyImage
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import asyncio
import re
import time
import pandas as pd
import dataframe_image as dfi

async def main():
  async with async_playwright() as p:

    def get_nikke_info(html):
    
      nikke_list = {
        "坎西:逃生女王":403,
        "魯德米拉:冬日之主":194,
        "海倫":352,
        "布雷德":520,
        "毒蛇":112,
        "潘托姆":580,
        "吉蘿婷:寒冬殺手":182,
  
        "愛麗絲":191,
        "明日香":830,
        "零":831,
        "神罰":260,
        "米哈拉: 羈絆鎖鏈":162,
        "拉毗:小紅帽":16,
        "格拉維":514,
        "德雷克":101,
  
        "紅蓮:暗影":225,
        "明日香：威爾":835,
        "小美人魚":513,
        "櫻花: 夏日綻放":284,
        "諾亞爾":271,
        "瑪娜":290,
        "零(暫稱)":834,
  
        "灰姑娘":511,
        "梅登:冰玫瑰":183,
        "阿妮斯: 閃耀夏日":15,
        "愛因":391,
        "伊莎貝爾":231,
        "紅蓮":222,
        "哈蘭":230,
        "普麗瓦蒂:不友善的女僕":313,
  
        "白雪公主":220,
        "小紅帽":470,
        "麥斯威爾":102,
        "索達:閃亮兔女郎":314,
      }

      line = []

      soup = BeautifulSoup(html, 'html.parser')

      # 1.妮姬名
      name_span = soup.find('div', class_='charinfo-name')
      if name_span and name_span.find('span'):
        name = name_span.find('span').get_text(strip=True)
      else:
        name = None
      line.append(name)

      # 2.突破判斷
      evolve_div = soup.find('div', class_='upgrade-evolve')

      evolve_result = None

      if evolve_div:
        evolve_p = evolve_div.find('p', class_='evolve')
        if evolve_p:
          span = evolve_p.find('span')
          if span:
            evolve_text = span.get_text(strip=True).lower()
            if evolve_text in ['max', '1', '2', '3', '4', '5', '6']:
              evolve_result = f'core {evolve_text}'

        if evolve_result is None:
          p_tags = evolve_div.find_all('p', class_=lambda x: x and 'upgrade-star' in x)
          for i in reversed(range(len(p_tags))):
            p_class = p_tags[i].get('class', [])
            if 'gold' in p_class:
              evolve_result = f'star {i+1}'
              break
          else:
            evolve_result = None
      line.append(evolve_result)

      # 3.屬性判斷
      img_tag = soup.find('img', class_='hex-border-dark')

      attribute = None

      if img_tag and img_tag.has_attr('src'):
        src = img_tag['src']
        if 'electronic' in src:
          attribute = '電擊'
        elif 'fire' in src:
          attribute = '燃燒'
        elif 'water' in src:
          attribute = '水冷'
        elif 'wind' in src:
          attribute = '風壓'
        elif 'iron' in src:
          attribute = '鐵甲'
        else:
          attribute = None
      else:
        attribute = None

      line.append(attribute)

      # 4.技能
      weapon_blocks = soup.find_all('div', class_='nikkes-weapon-res-left')

      if not weapon_blocks:
        line.extend([None, None, None])
      else:
        for block in weapon_blocks:
          spans = block.find_all('span', class_='text-20 text-white ff-num text-highlight-blue')
          for span in spans:
            value = span.get_text(strip=True)
            if value.isdigit():
              line.append(int(value))
            else:
              line.append(value)

      # 5.娃娃
      div1 = soup.find('div', class_='bg-[#454545] rounded-sm text-[color:#fff] text-center h-[24px] leading-[24px] text-[length:14px]')
      text1 = div1.get_text(strip=True) if div1 else None

      div2 = soup.find('div', class_='text-[color:var(--color-6)] text-[length:10px] ml-[2px] leading-[10px] mt-[2px] leading-[12px] text-[12px]')
      text2 = None
      if div2:
        match = re.search(r'(\d+)', div2.get_text())
        if match:
          text2 = match.group(1)

      if text1 in (None, '', '-'):
        doll_result = None
      else:
        doll_result = f"{text1} {text2}".strip()

      line.append(doll_result)

      # 6.詞條
      affix_targets = ['【優越代碼傷害增加】', '【攻擊力增加】', '【最大裝彈數增加】', '【暴擊傷害增加】']

      affix_results = {}

      for t in affix_targets:
        affix_results[t] = None
      
        span = soup.find('span', string=t)
        if span:
          parent_div = span.find_parent('div', attrs={'data-cname': 'equip-effect'})
          if parent_div:
            spans = parent_div.find_all('span', class_='ff-num')
            if spans and len(spans) > 0:
              affix_results[t] = spans[-1].get_text(strip=True)

      line.append(affix_results['【優越代碼傷害增加】'])
      line.append(affix_results['【攻擊力增加】'])
      line.append(affix_results['【最大裝彈數增加】'])
      line.append(affix_results['【暴擊傷害增加】'])

      return line

    async def block_resources(route, request):
      #"image"
      if request.resource_type in ["media","stylesheet", "font"]:
        await route.abort()
      else:
        await route.continue_()

    browser = await p.chromium.launch(headless=True)

    context = await browser.new_context()

    # cookies
    cookies = [
      
    ]

    await context.add_cookies(cookies)

    page = await context.new_page()

    await page.route("**/*", block_resources)

    input_url = "https://www.blablalink.com/shiftyspad/home?uid=MjkxNTctMjgzOTYwMDI2NjMxNTkwNzYyNA==&openid=MjkxNTctMjgzOTYwMDI2NjMxNTkwNzYyNA=="

    uid = input_url.split("uid=")[1].split("&")[0] if "uid=" in input_url else None
    openid = input_url.split("openid=")[1].split("&")[0] if "openid=" in input_url else None
    if uid is None and openid is None:
      return
    else:
      if uid is None:
        uid = openid
      if openid is None:
        openid =uid

    results = []

    print(uid)
    print(openid)

    n = 0
    for name, nikke_id in nikke_list.items():

      await asyncio.sleep(0.1)

      check_url = (
        "https://www.blablalink.com/shiftyspad/nikke?nikke="
        +str(nikke_id)+
        "&uid="+uid+
        "&openid="+openid
      )

      await page.goto(check_url, wait_until="networkidle")
      await asyncio.sleep(2)

      try:
        #pass
        await page.wait_for_selector('ul > li:not(.lock):nth-child(1)', timeout=10000)
      except TimeoutError:
        print(n)
        print(f'沒有{name}')
        n = n + 1
        continue
        
      await asyncio.sleep(0.1)

      html = await page.content()
      
      await asyncio.sleep(0.1)

      line = get_nikke_info(html)

      await asyncio.sleep(0.1)

      results.append(line)

      n = n + 1
      print(n)
      print(line)

      await asyncio.sleep(0.5)

    await page.close()
    await context.close()

    columns = ['角色', '突破', '屬性', '技能1', '技能2', '爆裂', '娃娃', '優越代碼', '攻擊力', '最大裝彈數', '暴擊傷害增加']

    df = pd.DataFrame(results, columns=columns)

    excel_path = '/content/output.xlsx'
    df.to_excel(excel_path, index=False)


    for res in results:
      print(res)

await main()
