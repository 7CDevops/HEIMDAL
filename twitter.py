import csv
import ctypes
import datetime
import os
from snscrape.base import ScraperException
from datetime import date
import pandas as pd
import snscrape.modules.twitter as sntwitter
import logging

import MyApp

logger = logging.getLogger()


def handleTwitter(url=None, extract=None, savePath=None, screen=None):
    # Recherche par hashtag sur twitter
    # scraperTwitter = sntwitter.TwitterSearchScraper("#python")
    # Recherche par user sur twitter
    # scraperTwitter = sntwitter.TwitterUserScraper(url)
    # Recherche par id tweet sur twitter
    if str(url).__contains__("status"):
        scraperTwitter = sntwitter.TwitterTweetScraper(extract)
    else:
        scraperTwitter = sntwitter.TwitterUserScraper(extract)


    # mise en place du tableau de recupération des infos
    tweets = []
    accessible = True
    for i, tweet in enumerate(scraperTwitter.get_items()):
        if type(tweet) is not sntwitter.Tombstone:
            mediaNbView = ""
            mediaDuration = ""
            mediaUrl = ""
            mediaType = ""

            try:
                if not tweet.media.__eq__(None):
                    if (str(tweet.media[0])).upper().__contains__("PHOTO"):
                        photoData = (str(tweet.media[0]))
                        extension = photoData.split("format=")[1].split("&")[0]
                        mediaType = f"Photo.{extension}"
                        mediaUrl = photoData.split("fullUrl='")[1].split("',")[0]

                    if (str(tweet.media[0])).upper().__contains__("VIDEO"):
                        videoData = (str(tweet.media[0]))
                        mediaType = "Video"
                        mediaNbView = videoData.split("views=")[1].split(",")[0]
                        mediaDuration = videoData.split("duration=")[1].split(",")[0]
                        mediaUrl = videoData.split("VideoVariant(url='")[1].split("',")[0]

            except Exception as e:
                logger.error("Twitter" + str(e))
                accessible = False
                pass

            urlSplit = tweet.url.split('/')
            urlCompte = '/'.join(urlSplit[0:4])
            data = [url,
                    urlCompte,
                    date.today(),
                    tweet.id,
                    tweet.rawContent.replace("\n", "").replace("\r", ""),
                    tweet.likeCount,
                    tweet.retweetCount,
                    tweet.lang,
                    tweet.links,
                    tweet.viewCount,
                    tweet.replyCount,
                    tweet.quoteCount,
                    tweet.quotedTweet,
                    tweet.media,
                    mediaType,
                    mediaUrl,
                    mediaNbView,
                    mediaDuration,
                    tweet.mentionedUsers,
                    tweet.user.username,
                    tweet.user.created,
                    tweet.user.displayname,
                    tweet.user.id,
                    tweet.user.renderedDescription.replace("\n", "").replace("\r", ""),
                    tweet.user.location,
                    tweet.date]
            tweets.append(data)

            if i > 15:
                break
        else:
            logger.error("Contenu du tweet non accessible.")
            accessible = False

    if accessible:
        # tableau de résultats vers csv
        tweet_csv = pd.DataFrame(
            tweets, columns=["action_url", "utilisateur_url", "action_gdh", "action_observation", "produit_sujet", "likes", "retweet",
                             "produit_langue", "liens", "vues", "reponses", "citations", "tweet_cite",
                             "produit_type_contenu",
                             "media_type", " media_URL", "media_vues", "media_duration", "utilisateurs_mentionnés",
                             "compte_login", "compte_gdh_creation", "compte_pseudo", "compte_numero_compte_provider",
                             "compte_observation", "compte_localisation_declaree", "produit_gdh_saisie"]
        )
        try:
            pathFile = f"{savePath}/veille_ffs_twitter.csv"
            tweet_csv.to_csv(f"{savePath}/veille_ffs_twitter.csv", index=False, sep="|", quoting=csv.QUOTE_MINIMAL,
                             mode='a', header=not os.path.exists(pathFile), encoding="cp1252", errors='replace')
            # Mise à jour des labels pour afficher les résultats
            MyApp.VeilleScreen.twitterCount += 1
            MyApp.VeilleScreen.totalCount += 1
            MyApp.saveStats()

            MyApp.updateResultVeille(screen=screen)
        except Exception as e:
            logger.error("HandleTwitter : " + str(e))




def handleTwitterRecherche(valeur=None, maxTweets=None, type=None, savePath=None, screen=None):
    # differents types de Recherche twitter
    try:
        if type.__contains__("user"):
            scraperTwitter = sntwitter.TwitterProfileScraper(valeur)
        elif type.__contains__("tweet"):
            scraperTwitter = sntwitter.TwitterTweetScraper(valeur)
        elif type.__contains__("hashtag"):
            scraperTwitter = sntwitter.TwitterHashtagScraper(valeur)
        elif type.__contains__("search"):
            scraperTwitter = sntwitter.TwitterSearchScraper(valeur + ' since:' + MyApp.RechercheScreen.selectedDateDeb + ' until:' + MyApp.RechercheScreen.selectedDateFin)

        tweets = []
        for i, tweet in enumerate(scraperTwitter.get_items()):
            mediaNbView = ""
            mediaDuration = ""
            mediaUrl = ""
            mediaType = ""

            if i > (int(maxTweets) - 1):
                break

            try:
                if not tweet.media.__eq__(None):
                    if (str(tweet.media[0])).upper().__contains__("PHOTO"):
                        photoData = (str(tweet.media[0]))
                        extension = photoData.split("format=")[1].split("&")[0]
                        mediaType = f"Photo.{extension}"
                        mediaUrl = photoData.split("fullUrl='")[1].split("',")[0]

                    if (str(tweet.media[0])).upper().__contains__("VIDEO"):
                        videoData = (str(tweet.media[0]))
                        mediaType = "Video"
                        mediaNbView = videoData.split("views=")[1].split(",")[0]
                        mediaDuration = videoData.split("duration=")[1].split(",")[0]
                        mediaUrl = videoData.split("VideoVariant(url='")[1].split("',")[0]

            except Exception as e:
                logger.error("Twitter" + str(e))
                pass

            urlSplit = tweet.url.split('/')
            urlCompte = '/'.join(urlSplit[0:4])
            data = [tweet.url,
                    urlCompte,
                    date.today(),
                    tweet.id,
                    tweet.rawContent.replace("\n", "").replace("\r", ""),
                    tweet.likeCount,
                    tweet.retweetCount,
                    tweet.lang,
                    tweet.links,
                    tweet.viewCount,
                    tweet.replyCount,
                    tweet.quoteCount,
                    tweet.quotedTweet,
                    tweet.media,
                    mediaType,
                    mediaUrl,
                    mediaNbView,
                    mediaDuration,
                    tweet.mentionedUsers,
                    tweet.user.username,
                    tweet.user.created,
                    tweet.user.displayname,
                    tweet.user.id,
                    tweet.user.renderedDescription.replace("\n", "").replace("\r", ""),
                    tweet.user.location,
                    tweet.date.date()]
            tweets.append(data)

        # tableau de résultats vers csv
        tweet_csv = pd.DataFrame(
            tweets, columns=["action_url", "utilisateur_url",  "action_gdh","action_observation", "produit_sujet", "likes", "retweet",
                             "produit_langue", "liens", "vues", "reponses", "citations", "tweet_cite","produit_type_contenu",
                             "media_type", " media_URL", "media_vues", "media_duration", "utilisateurs_mentionnés",
                             "compte_login", "compte_gdh_creation", "compte_pseudo", "compte_numero_compte_provider",
                             "compte_observation","compte_localisation_declaree","produit_gdh_saisie",]
        )
        try:
            if (len(tweet_csv) > 0):
                try:
                    if not os.path.exists(savePath + "/recherche_twitter"):
                        os.makedirs(savePath + "/recherche_twitter")
                except Exception as error:
                    logger.error("Problème lors de la création du répertoire recherche_twitter" + str(error))
                    ctypes.windll.user32.MessageBoxW(0, "Erreur de la création du répertoire recherche_twitter", "Erreur")

                tweet_csv.to_csv(f"{savePath}/recherche_twitter/export_tweets_{type}_{valeur}_{maxTweets}.csv", index=False, sep="|",
                                 quoting=csv.QUOTE_MINIMAL, mode='a',   encoding="cp1252", errors='replace')
                MyApp.RechercheScreen.textResult = f"Le fichier export_tweets_{type}_{valeur}_{maxTweets}.csv a été créé \ndans le répertoire recherche_twitter de votre dossier de partage"
                MyApp.updateResultSearch(screen=screen)
            else:
                MyApp.RechercheScreen.textResult = "Aucun résultat"
                MyApp.updateResultSearch(screen=screen)

        except Exception as e:
            logger.error(e)
            MyApp.RechercheScreen.textResult = e
    except ScraperException:
        logger.error("error scraper suite à une recherche ou mauvaise saisie utilisateur")
        MyApp.RechercheScreen.textResult = "Aucun résultat. Mauvaise recherche ou erreur du scrapper"
        MyApp.updateResultSearch(screen=screen)




