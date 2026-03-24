from openai import OpenAI
from config import OPENAI_API_KEY, CATEGORY_EMOJI

client = OpenAI(api_key=OPENAI_API_KEY)

def build_cluster_context(cluster):
    lines = []
    for i, article in enumerate(cluster["articles"][:5], start=1):
        lines.append(f"{i}. Majiya: {article['source']}")
        lines.append(f"   Take: {article['title']}")
        if article["summary"]:
            lines.append(f"   Bayani: {article['summary']}")
    return "\n".join(lines)

def generate_new_story_post(cluster):
    emoji = CATEGORY_EMOJI.get(cluster["category"], "🗞")
    urgent_tag = "⚡ " if cluster.get("breaking") else ""
    context = build_cluster_context(cluster)

    prompt = f'''
Kai kwararren editan labarai ne na Hausa irin salon BBC Hausa.
A kasa akwai rahotanni da dama kan labari iri daya daga majiyoyi daban-daban.

Aikinka:
- Hada su cikin labari guda mai karfi
- Ka fitar da ainihin abin da ya faru
- Kada ka kirkiri bayanai
- Kada ka saka link
- Kada ka yi hayaniya
- Ka yi Hausa mai tsabta, mai sauki, mai nagarta
- Ka nuna muhimmancin labarin
- Ka nuna abin da Najeriya za ta iya koya ko lura da shi

Ka dawo da amsa a wannan tsari kawai:

{urgent_tag}{emoji} {cluster["category"].upper()}

Takaitaccen bayani:
[Jimloli 2 zuwa 4]

Dalilin da ya sa wannan yake da muhimmanci:
[Layi 1]

Abin da Najeriya za ta iya koya:
[Layi 1]

Manyan majiyoyi:
[Rubuta sunayen manyan majiyoyi 2 zuwa 4 kacal, a layi daya]

Ga bayanan da aka tattara:
{context}
'''

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a BBC-grade Hausa newsroom editor. Write natural, serious, polished Hausa. Merge overlapping reports into one clean bulletin."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

def generate_update_post(cluster, previous_headline, previous_summary):
    urgent_tag = "⚡ " if cluster.get("breaking") else ""
    context = build_cluster_context(cluster)

    prompt = f'''
Kai kwararren editan labarai ne na Hausa irin salon BBC Hausa.
Wannan labari ya taba fitowa a baya, amma yanzu akwai sabon ci gaba.

Bayanan baya:
Take na baya: {previous_headline}
Takaitaccen bayanin baya: {previous_summary}

A kasa akwai sabbin bayanai daga majiyoyi daban-daban.

Aikinka:
- Ka rubuta wannan a matsayin sabuwar sanarwar ci gaba
- Kada ka maimaita tsohon labari gaba daya
- Ka nuna me ya canza ko me ya karu
- Ka yi Hausa mai tsabta, mai sauki, mai nagarta
- Kada ka yi hayaniya
- Kada ka kirkiri bayanai
- Ka saka layi daya kan abin da Najeriya za ta lura da shi

Ka dawo da amsa a wannan tsari kawai:

{urgent_tag}🔁 SABON BAYANI — {cluster["category"].upper()}

Sabon abin da ya faru:
[Jimloli 2 zuwa 3]

Me ya canza yanzu:
[Layi 1]

Abin da Najeriya za ta lura da shi:
[Layi 1]

Manyan majiyoyi:
[Rubuta sunayen manyan majiyoyi 2 zuwa 4 kacal, a layi daya]

Ga sabbin bayanan da aka tattara:
{context}
'''

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a BBC-grade Hausa newsroom editor. Write polished, serious Hausa. Frame this as an update to an earlier story, not a completely new bulletin."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()
