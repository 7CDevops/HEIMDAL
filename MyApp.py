import logging
import sys
from datetime import datetime
import os

from selenium.common import InvalidSessionIdException

# Create and configure logger
# Cette configuration doit se faire avant la configuration graphic de la fenêtre
exePath = sys.executable.split("\\Heimdall.exe")[0]
try:
    os.makedirs(exePath + "/LOG/", exist_ok=True)
except FileNotFoundError:
    exePath = os.getcwd()
    os.makedirs(exePath + "/LOG/", exist_ok=True)
logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    filemode='w',
    filename=f'{exePath}/LOG/Heimdall_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.log',
    level=logging.INFO)
logger = logging.getLogger()
#empeche kivy de log
os.environ["KIVY_NO_FILELOG"]="1"

from kivy import LOG_LEVELS

import threading
from os.path import exists
from tkinter import Tk
from tkinter.filedialog import askdirectory
from kivy.config import Config
# Les configurations doivent être déclarées en premier avant tous les imports suivants
Config.set('graphics', 'resizable', '1')  # 0 being off 1 being on as in true/false
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '540')
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.properties import NumericProperty, StringProperty
from kivymd.uix.pickers import MDTimePicker, MDDatePicker
import twitter
from whatsapp import WhatsApp
import ctypes
logger.setLevel(LOG_LEVELS["info"])


# Ecran principal
class CustomTextInput(TextInput):
    text_width = NumericProperty()

    def update_padding(self):
        self.text_width = self._get_text_width(
            self.text,
            self.tab_width,
            self._label_cached
        )

# Class custom redéfinissant les TextInput
class RoundedInput(TextInput):
    text_width = NumericProperty()

    def update_padding(self):
        self.text_width = self._get_text_width(
            self.text,
            self.tab_width,
            self._label_cached
        )

def end_func(self):
    os.system("taskkill /im chrome.exe /f")
    MyApp.stop(MyApp.get_running_app())
    Window.close()
    logger.info("Fermeture de Heimdall par l'utilisateur")




class VeilleScreen(Screen):
    session = None
    savePath = ""
    image_source = StringProperty()
    pathStats = f'{os.getcwd()}\\Configuration\\stats.txt'
    totalCount = facebookCount = twitterCount = 0
    rapportIsDone = False

    def __init__(self, **kwargs):
        super(VeilleScreen, self).__init__(**kwargs)
        # binding pour capter l'évènement de fermeture de la fenêtre principale par l'utilisateur
        self.image_source = resource_path(r'Images\fond.jpg')
        loadStats()

    def disableButton(self):
        self.ids.LaunchButton.disabled = True

    def stopWhatsAppSession(self):
        try:
            self.ids.LaunchButton.disabled = False
            if self.session is not None:
                self.session.browser.close()
        except InvalidSessionIdException as invalidSession:
            logger.error("StopWhatsAppSession : " + str(invalidSession))


    def listeningWhatsAppSession(self):
        # Appel de la méthode pour l'écoute des conversations.
        #recupération des infos connexions chromeuserdata et
        if os.path.exists("Configuration\config.txt"):
            with open(f"{os.getcwd()}\Configuration\config.txt", "r") as file:
                values = list(file.read().split("\n"))
                session = values[0]
                savePath = values[1]
                file.close()
                logger.info("Recupération chemins de session et partage")
        else:
            logger.error("Fichier de configuration inexistant")

        #controle si les chemins existent
        if not os.path.exists(session):
            self.ids.LaunchButton.disabled = False
            ctypes.windll.user32.MessageBoxW(0, "Le chemin de la session n'est pas connu sous windows merci de le modifier dans l'onglet Parametres ", "Erreur")
        if not os.path.exists(savePath):
            self.ids.LaunchButton.disabled = False
            ctypes.windll.user32.MessageBoxW(0, "Windows ne connait pas le chemin renseigné pour la sauvegarde du fichier csv voir l'onglet Parametres", "Erreur")
        elif len(savePath) == 0:
            self.ids.LaunchButton.disabled = False
            ctypes.windll.user32.MessageBoxW(0, "Un chemin vers un répertoire de sauvegarde est obligatoire voir l'onglet Parametres", "Erreur")

        else:

            try:
                os.makedirs(savePath, exist_ok=True)
            except Exception as e:
                logger.error(e)
                ctypes.windll.user32.MessageBoxW(0, "Erreur lors de la tentative de sauvegarde de la session WhatsApp",
                                                 "Erreur")

            # threading.Thread(target=, args=()).start()
            self.session = WhatsApp(wait=999999, session=session, screen=self)
            logger.info("Lancement de la session")
            #mysession = [self.session, savePath]
            #self.saveConfiguration()
            #self.session.listenNewMessage(savePath=savePath)
            listenthread = threading.Thread(name="listen", target=self.session.listenNewMessage, args=(savePath,)).start()

# Sauvegarde des stats.
def saveStats():
    # chemin vers le répertoire de stockage du fichier de configuration
    VeilleScreen.pathStats = f'{os.getcwd()}\Configuration'
    # sauvegarde de fichier avec les configurations, s'il n'existe pas il est créé par la fonction open()
    if not os.path.exists(VeilleScreen.pathStats):
        ctypes.windll.user32.MessageBoxW(0,
                                         "Le répertoire Configuration n'est pas présent dans le répertoire de HEIMDALL.\n"
                                         "Veuillez le recréer ou procéder à une nouvelle installation",
                                         "Erreur")
        return
    try:
        with open(VeilleScreen.pathStats + "\stats.txt", 'w') as file:
            file.write(
                str(VeilleScreen.totalCount) + "\n" +
                str(VeilleScreen.twitterCount) + "\n" +
                str(VeilleScreen.facebookCount) + "\n" +
                str(VeilleScreen.rapportIsDone)
            )
            file.close()
    except Exception as error:
        logger.error("Problème lors de la sauvegarde des stats " + str(error))
        ctypes.windll.user32.MessageBoxW(0, "Erreur lors de la sauvegarde des stats", "Erreur")

# load des stats.
def loadStats():
    # chemin vers le répertoire de stockage du fichier de configuration
    VeilleScreen.pathStats = f'{os.getcwd()}\Configuration'
    # sauvegarde de fichier avec les configurations, s'il n'existe pas il est créé par la fonction open()
    if not os.path.exists(VeilleScreen.pathStats):
        ctypes.windll.user32.MessageBoxW(0,
                                         "Le répertoire Configuration n'est pas présent dans le répertoire de HEIMDALL.\n"
                                         "Veuillez le recréer ou procéder à une nouvelle installation",
                                         "Erreur")
        return
    try:
        with open(VeilleScreen.pathStats + "\stats.txt", 'r') as file:
            values = list(file.read().split("\n"))
            VeilleScreen.totalCount = int(values[0])
            VeilleScreen.twitterCount = int(values[1])
            VeilleScreen.facebookCount = int(values[2])
            if (values[3]=="True"):
                VeilleScreen.rapportIsDone = True
            else:
                VeilleScreen.rapportIsDone = False
            file.close()
            logger.info("Chargement des stats")
    except Exception as error:
        logger.error("Problème lors du chargement des stats " + str(error))
        saveStats()


# Mise à jour des labels pour afficher un résultat à l'utilisateur
def updateResultVeille(screen=None):
    screen.ids.labelTotalCount.text = "Total messages : " + str(VeilleScreen.totalCount)
    screen.ids.labelTwitterCount.text = "Liens Twitter traités : " + str(VeilleScreen.twitterCount)
    screen.ids.labelFacebookCount.text = "Liens Facebook traités : " + str(VeilleScreen.facebookCount)

def updateResultSearch(screen=None):
    screen.ids.labelAfficheSearch.text = str(RechercheScreen.textResult)


class RechercheScreen(Screen):
    savePath = ""
    image_source = StringProperty()
    textResult = ""
    selectedDateDeb = selectedDateFin = ''

    def __init__(self, **kwargs):
        super(RechercheScreen, self).__init__(**kwargs)
        # binding pour capter l'évènement de fermeture de la fenêtre principale par l'utilisateur
        self.image_source = resource_path(r'Images\fond.jpg')

    def disableButton(self):
        self.ids.SearchButton.disabled = True

    def searchTweets(self):
        # Appel de la méthode pour l'écoute des conversations.
        # recupération des infos connexions chromeuserdata et
        if os.path.exists("Configuration\config.txt"):
            with open(f"{os.getcwd()}\Configuration\config.txt", "r") as file:
                values = list(file.read().split("\n"))
                savePath = values[1]
                file.close()
                logger.info("Récupération dossier partage pour sauvagarde tweets")
        else:
            logger.error("Fichier de configuration inexistant")

        # controle si le chemin de sauvegarde existe
        if not os.path.exists(savePath):
            ctypes.windll.user32.MessageBoxW(0,
                                             "Windows ne connait pas le chemin renseigné pour la sauvegarde du fichier csv voir l'onglet Parametres",
                                             "Erreur")
            self.ids.SearchButton.disabled = False
        elif len(savePath) == 0:
            ctypes.windll.user32.MessageBoxW(0,
                                             "Un chemin vers un répertoire de sauvegarde est obligatoire voir l'onglet Parametres",
                                             "Erreur")
            self.ids.SearchButton.disabled = False

        else:

            try:
                os.makedirs(savePath, exist_ok=True)
            except Exception as e:
                logger.error(e)
                ctypes.windll.user32.MessageBoxW(0, "Erreur lors de la tentative de sauvegarde de la session WhatsApp",
                                                 "Erreur")
                self.ids.SearchButton.disabled = False

        typeRecherche = "";
        maxTweets = self.ids.maxTweetsInput.text
        valeur = self.ids.valeurInput.text
        if (self.ids.cbUser.active):
            typeRecherche = "user"
        elif (self.ids.cbTweet.active):
            typeRecherche = "tweet"
            maxTweets = 1
        elif (self.ids.cbHashtag.active):
            typeRecherche = "hashtag"
        elif (self.ids.cbSearch.active):
            typeRecherche = "search"

        #controle des champs de saisie lors de la recherche twitter
        if valeur != "":
            if not self.ids.cbTweet.active:
                if self.ids.cbHashtag.active and "#" in valeur:
                    ctypes.windll.user32.MessageBoxW(0, "Veuillez enlever # pour votre recherche par hashtag", "Erreur")
                    logger.info("Mauvaise saisie du champ maxtweets")
                    self.ids.SearchButton.disabled = False
                else:
                    try:
                        maxTweets = int(maxTweets)
                    except Exception as e:
                        ctypes.windll.user32.MessageBoxW(0,"Veuillez entrer un nombre pour Max tweets","Erreur")
                        logger.info("Mauvaise saisie du champ maxtweets")
                        self.ids.SearchButton.disabled = False
                    twitter.handleTwitterRecherche(valeur, maxTweets, typeRecherche, savePath,
                                                   screen=self)
            else:
                try:
                    valeur = int(valeur)
                    twitter.handleTwitterRecherche(valeur, maxTweets, typeRecherche, savePath,
                                                   screen=self)
                except Exception as e:
                    ctypes.windll.user32.MessageBoxW(0, "Veuillez entrer un nombre pour le numéro de tweet", "Erreur")
                    logger.info("Mauvaise saisie du champ maxtweets")
                    self.ids.SearchButton.disabled = False
        else:
            ctypes.windll.user32.MessageBoxW(0, "Veuillez entrer une valeur de recherche","Erreur")
            logger.info("Aucune valeur dans l'inputtext Valeur de l'onglet Recherche twitter")
            self.ids.SearchButton.disabled = False

        self.ids.SearchButton.disabled = False

    # Création et affichage du composant timePicker
    def show_calendar_pickerDateDeb(self):
        # Instanciation du DatePicker
        date_dialog = MDDatePicker()
        # binding des méthodes on_save et on_cancel sur les méthodes déclarées au-dessus.
        date_dialog.bind(on_save=self.on_saveDateDeb, on_cancel=self.on_cancelDateDeb)
        # Application thème Dark
        date_dialog.theme_cls.theme_style = "Dark"
        date_dialog.open()

        # Création et affichage du composant timePicker
    def show_calendar_pickerDateFin(self):
        # Instanciation du DatePicker
        date_dialog = MDDatePicker()
        # binding des méthodes on_save et on_cancel sur les méthodes déclarées au-dessus.
        date_dialog.bind(on_save=self.on_saveDateFin, on_cancel=self.on_cancelDateFin)
        # Application thème Dark
        date_dialog.theme_cls.theme_style = "Dark"
        date_dialog.open()


    # Gestion d'annulation de la date de debut
    def on_cancelDateDeb(self, instance, value):
        self.ids.dateDeb.text = ""
        try:
            RechercheScreen.selectedDateDeb = ""
        except Exception as e:
            print(e)

    # Gestion d'annulation de la date de fin
    def on_cancelDateFin(self, instance, value):
        self.ids.dateFin.text = ""
        try:
            RechercheScreen.selectedDateFin = ""
        except Exception as e:
            print(e)

    # Sauvegarde de la date de début recherche twitter
    def on_saveDateDeb(self, instance, value, date_range):
        # Affichage du temps sélectionné dans l'interface avec le composant dédié
        try:
            RechercheScreen.selectedDateDeb = str(value)
            self.ids.dateDeb.text = str(value)
        except Exception as e:
            print(e)

        # Sauvegarde du temps sélectionné dans l'horloge par l'utilisateur

    def on_saveDateFin(self, instance, value, date_range):
        # Affichage du temps sélectionné dans l'interface avec le composant dédié
        try:
            RechercheScreen.selectedDateFin = str(value)
            self.ids.dateFin.text = str(value)
        except Exception as e:
            print(e)

    def showInputSearch(self):
        self.ids.labelMaxTweets.text = "Max Tweets :"
        self.ids.maxTweetsInput.disabled = False
        self.ids.maxTweetsInput.opacity = 1
        self.ids.buttonDateDeb.disabled = False
        self.ids.buttonDateDeb.opacity = 1
        self.ids.dateDeb.disabled = False
        self.ids.dateDeb.opacity = 1
        self.ids.dateFin.disabled = False
        self.ids.dateFin.opacity = 1
        self.ids.buttonDateFin.disabled = False
        self.ids.buttonDateFin.opacity = 1
        self.ids.labelDateFin.text = "Date Fin :"
        self.ids.labelDateDeb.text = "Date Début :"

    def showInputNomUser(self):
        self.ids.labelMaxTweets.text = "Max Tweets :"
        self.ids.maxTweetsInput.disabled = False
        self.ids.maxTweetsInput.opacity = 1
        self.ids.buttonDateDeb.disabled = True
        self.ids.buttonDateDeb.opacity = 0
        self.ids.dateDeb.disabled = True
        self.ids.dateDeb.opacity = 0
        self.ids.dateFin.disabled = True
        self.ids.dateFin.opacity = 0
        self.ids.buttonDateFin.disabled = True
        self.ids.buttonDateFin.opacity = 0
        self.ids.labelDateFin.text = ""
        self.ids.labelDateDeb.text = ""

    def showInputNumeroTweet(self):
        self.ids.labelMaxTweets.text = ""
        self.ids.maxTweetsInput.disabled = True
        self.ids.maxTweetsInput.opacity = 0
        self.ids.buttonDateDeb.disabled = True
        self.ids.buttonDateDeb.opacity = 0
        self.ids.dateDeb.disabled = True
        self.ids.dateDeb.opacity = 0
        self.ids.dateFin.disabled = True
        self.ids.dateFin.opacity = 0
        self.ids.buttonDateFin.disabled = True
        self.ids.buttonDateFin.opacity = 0
        self.ids.labelDateFin.text = ""
        self.ids.labelDateDeb.text = ""

    def showInputHashtag(self):
        self.ids.labelMaxTweets.text = "Max Tweets :"
        self.ids.maxTweetsInput.disabled = False
        self.ids.maxTweetsInput.opacity = 1
        self.ids.buttonDateDeb.disabled = True
        self.ids.buttonDateDeb.opacity = 0
        self.ids.dateDeb.disabled = True
        self.ids.dateDeb.opacity = 0
        self.ids.dateFin.disabled = True
        self.ids.dateFin.opacity = 0
        self.ids.buttonDateFin.disabled = True
        self.ids.buttonDateFin.opacity = 0
        self.ids.labelDateFin.text = ""
        self.ids.labelDateDeb.text = ""

class ParametresScreen(Screen):
    session = ""
    savePath = ""
    image_source = StringProperty()
    selectedTime = ''
    messageSupp = ""

    def __init__(self, **kwargs):
        super(ParametresScreen, self).__init__(**kwargs)
        # binding pour capter l'évènement de fermeture de la fenêtre principale par l'utilisateur
        self.image_source = resource_path(r'Images\fond.jpg')


    def saveConfiguration(self):
        with open(f"{os.getcwd()}\Configuration\config.txt", "w") as file:
            file.write(
                str(self.ids.sessionInput.text) + "\n" +
                str(self.ids.savePathInput.text) + "\n" +
                str(self.ids.messageInput.text) + "\n" +
                str(self.ids.inputTime.text)
            )
            file.close()
            logger.info("Sauvegarde de la configuration")

    def open_explorer_session(self):
        try:
            Tk().withdraw()  # Suppression de l'interface principale qui s'affiche par default dès l'exécution d'un composant Tkinter
            dossierChoisi = askdirectory()
            if dossierChoisi != "":
                self.ids.sessionInput.text = dossierChoisi
                logger.info(f"Nouveau chemin de session WhatsApp  : {self.ids.sessionInput.text} ")
                self.saveConfiguration()
        except IndexError:
            logger.warning("Session : Chemin inconnu")

    def open_explorer_partage(self):
        try:
            Tk().withdraw()  # Suppression de l'interface principale qui s'affiche par default dès l'exécution d'un composant Tkinter
            dossierChoisi = askdirectory()
            if dossierChoisi != "":
                self.ids.savePathInput.text = dossierChoisi
                logger.info(f"Nouveau chemin de partage  : {self.ids.savePathInput.text} ")
                self.saveConfiguration()
        except IndexError:
            logger.warning("Partage : Chemin inconnu")

    # Sauvegarde du temps sélectionné dans l'horloge par l'utilisateur
    def on_saveTime(self, instance, value):
        # Affichage du temps sélectionné dans l'interface avec le composant dédié
        self.ids.inputTime.text = str(value)
        try:
            self.selectedTime = datetime.strptime(str(value), "%H:%M:%S").time()
        except Exception as e:
            print(e)
        logger.info(f"Nouvelle heure rapport  : {self.ids.inputTime.text} ")
        self.saveConfiguration()

    # Gestion d'annulation de la sélection par l'utilisateur
    def on_cancelTime(self, instance, value):
        pass

    # Création et affichage du composant timePicker
    def show_time_picker(self):
        # Instanciation du TimePicker
        time_dialog = MDTimePicker()
        # binding des méthodes on_save et on_cancel sur les méthodes déclarées au-dessus.
        time_dialog.bind(on_save=self.on_saveTime, on_cancel=self.on_cancelTime)
        # Application thème Dark
        time_dialog.theme_cls.theme_style = "Dark"
        time_dialog.open()

    # Ajout d'un message au rapport
    def save_message_rapport(self):
        self.messageSupp = self.ids.messageInput.text
        self.saveConfiguration()


def loadConfiguration(self):
    if os.path.exists("Configuration\config.txt"):
        with open(f"{os.getcwd()}\Configuration\config.txt", "r") as file:
            values = list(file.read().split("\n"))
            self.ids.manager.ids.parametres.ids.sessionInput.text = values[0]
            self.ids.manager.ids.parametres.ids.savePathInput.text = values[1]
            self.ids.manager.ids.parametres.ids.messageInput.text = values[2]
            self.ids.manager.ids.parametres.ids.inputTime.text = values[3]

            file.close()
            logger.info("Chargement de la configuration")
    else:
        logger.error("Fichier de configuration inexistant")

# Méthode pour focus la fenêtre principale quand le curseur passe dessus afin d'éviter d'avoir un clique obligatoire pour focus la fenêtre.
def window_callback(self):
    if not Window.focus:
        Window.raise_window()
        #point = pyautogui.position()
        #pyautogui.click(Window.top)
        #pyautogui.move(point)

# Gestionnaire de vue dans l'application dans le fichier .kv
class ScreenManagement(ScreenManager):
    pass

# Class principal du fichier MyApp.kv
class MainScreen(BoxLayout):
    # Constructeur
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        # binding pour capter l'évènement de fermeture de la fenêtre principale par l'utilisateur
        Window.bind(on_request_close=end_func)
        Window.bind(on_cursor_enter=window_callback)
        loadConfiguration(self)

# Méthode pour récupérer le chemin d'une ressource notamment lors de l'exécution depuis un exécutable.
# Si exécution en environnement de dev, renvoi du chemin de stockage.
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception as error:
        base_path = os.path.abspath(".")
        logger.error(str(error))
    return os.path.join(base_path, relative_path)

class MyApp(MDApp):

    # Construction
    def build(self):
        self.title = "HEIMDALL - 1.0.1"
        self.icon = resource_path(r'Images\noir.ico')
        # Renvoi une instance de l'écran principal
        return MainScreen()


if __name__ == '__main__':
    # Lancement de l'application
    logger.info("Lancement de l'application")
    MyApp().run()
