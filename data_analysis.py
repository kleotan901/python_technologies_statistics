import matplotlib.pyplot as plt
import nltk
import pandas as pd
import seaborn as sns
from pandas import DataFrame
from wordcloud import WordCloud

import config


def get_count_technologies() -> DataFrame:
    jobs_text = pd.read_csv("jobs.csv")
    text = " ".join(jobs_text["description"].astype(str))
    tokens = nltk.word_tokenize(text)
    pos_tags = nltk.pos_tag(tokens)

    technologies_dict = {}
    for techs_tuple in pos_tags:
        if techs_tuple[0] not in config.exclude_words:
            if techs_tuple[1] == "NNP" and techs_tuple[0] in technologies_dict:
                technologies_dict[techs_tuple[0]] += 1
            if techs_tuple[1] == "NNP" and techs_tuple[0] not in technologies_dict:
                technologies_dict[techs_tuple[0]] = 1

    technologies_count_df = pd.DataFrame(
        list(technologies_dict.items()), columns=["Technology", "Popularity"]
    ).sort_values("Popularity", ascending=False)

    return technologies_count_df


def diagram_of_popular_technologies() -> None:
    technologies = get_count_technologies().head(20)

    plt.figure(figsize=(10, 7))
    plt.bar(technologies["Technology"], technologies["Popularity"], width=0.5)
    plt.xticks(technologies["Technology"], rotation="vertical")
    plt.show()


def correlation_diagram():
    technologies = pd.read_csv("jobs.csv")
    technologies_corr = technologies[["experience", "views", "applications"]]
    sns.heatmap(technologies_corr.corr(), annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation Heatmap")
    plt.show()


def generate_wordcloud():
    technologies_df = get_count_technologies().head(20)
    technologies = " ".join(technologies_df["Technology"].astype(str))

    wordcloud = WordCloud(
        width=800, height=400, random_state=21, max_font_size=110
    ).generate(technologies)

    plt.figure(figsize=(10, 7))
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    diagram_of_popular_technologies()
    correlation_diagram()
    generate_wordcloud()
