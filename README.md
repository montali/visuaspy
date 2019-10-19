<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/simmontali/visuaspy">
    <img src="res/sunglasses.png" alt="Logo" width="130" height="130">
  </a>
  <h1 align="center">VisuaSpy</h1>

  <p align="center">
    Instagram spies catcher.  
  </p>
</p>



<!-- TABLE OF CONTENTS -->
## Table of Contents

- [Table of Contents](#table-of-contents)
- [About The Project](#about-the-project)
  - [How it works](#how-it-works)
- [Getting Started](#getting-started)
  - [Updates](#updates)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)



<!-- ABOUT THE PROJECT -->
## About The Project
![Product Name Screen Shot][screenshot]

**VisuaSpy** was born to find your Instagram *stalkers*, a.k.a. users that view your stories but don't follow you. It is meant to be used as a cronjob. In the past, experiments using the algorithm in a public bot were done. People didn't use it so here we are back on the public side of GitHub!
### How it works
**VisuaSpy** uses the [Instagram Private API project](https://github.com/ping/instagram_private_api) to fetch your story viewers. It then compares it to your followers/following, and only presents it if you're not following each other, but you have mutual followers *(Hating those fashion bloggers with story viewing bots)*.



<!-- GETTING STARTED -->
## Getting Started

You can just clone this repository, install the requirements by running
```
$ pip3 install -r requirements.txt
```
and then start VisuaSpy.

### Updates
Pull this repository for updates.

<!-- USAGE EXAMPLES -->
## Usage

To run VisuaSpy with a Telegram bot, run
```
 $ python3 stalkers.py -u "[YOUR_USER_HERE]" -p "[YOUR_PASSWORD_HERE]" -settings "[COOKIE_FILENAME_HERE]" -t "[TELEGRAM_BOT_API_KEY]" -c [YOUR_TELEGRAM_CHAT_ID]
```
These parameters are:
* `-u` your Instagram user
* `-p` your Instagram password
* `-settings` your cookie file name. For the first run, you can insert a random `name.json`.
* `-t` is your Telegram Bot API key, get it from the BotFather.
* `-c` is your Telegram chat ID. It will be printed on the console when you `\start` the bot.

To run VisuaSpy without Telegram, just run
```
 $ python3 stalkers.py -u "[YOUR_USER_HERE]" -p "[YOUR_PASSWORD_HERE]" -settings "[COOKIE_FILENAME_HERE]"
```
with these parameters:
* `-u` your Instagram user
* `-p` your Instagram password
* `-settings` your cookie file name. For the first run, you can insert a random `name.json`.



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## Stalkers cleaning
```
"stalkers": \[[a-zA-Z.\-_\d", ]*\]
```
<!-- LICENSE -->
## License

Distributed under the GPL License. See `LICENSE` for more information.
<div>Icon made by <a href="https://www.flaticon.com/authors/freepik" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/"             title="Flaticon">www.flaticon.com</a></div>


<!-- CONTACT -->
## Contact

[Simone Montali](https://monta.li)

Project Link: [https://github.com/simmontali/VisuaSpy](https://github.com/simmontali/visuaspy)

[screenshot]: res/screenshot.gif "Screenshot"
[logo]: res/sunglasses.png
