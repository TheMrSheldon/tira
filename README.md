<h1 align="center">TIRA</h1>

<p align="center">
   <img src="https://github.com/tira-io/tira-branding/raw/master/tira-icons/logo-tira-120x120-transparent.png">
   <!--h3>Integrated Research Architecture</h3-->
   <br/>
   <br/>
   <a href="https://github.com/tira-io/tira">
   <img alt="GPL 2.0 License" src="https://img.shields.io/github/license/tira-io/tira.svg"/>
   </a>
   <a href="https://github.com/tira-io/tira/releases">
   <img alt="Current Release" src="https://img.shields.io/github/release/tira-io/tira.svg"/>
   </a>
   <a href="https://github.com/tira-io/tira/releases">
   <img alt="Backend Test Coverage" src="application/test/test-coverage/coverage.svg"/>
   </a>
   <a href="https://tira.io">
   <img alt="Deployment" src="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fwww.tira.io%2Fapi%2Fv1%2F&query=%24.version&prefix=v.&label=tira.io"/>
   </a>
   <br>
   <a href="https://tira-io.github.io/tira/">Documentation</a> &nbsp;|&nbsp;
   <a href="./application/">Backend</a> &nbsp;|&nbsp;
   <a href="./frontend/">Frontend</a> &nbsp;|&nbsp;
   <a href="./python-client/">API &amp; CLI</a> &nbsp;|&nbsp;
   <a href="https://webis.de/publications.html?q=tira">Publications</a> &nbsp;|&nbsp;
   <a href="#citation">Citation</a>
</p>

---

TIRA **I**ntegrated **R**esearch **A**rchitecture is a free and open source research platform designed for hosting and
partaking in shared tasks of varied nature.

## I want to...
### ... organize a shared task
`TODO`

### ... deploy my own instance
`TODO`

### ... join a shared task
`TODO`

### ... contribute (bug reports, feature requests, code, documentation)
Great! Check out our <a href="">Contribution Guide</a>.

---

<!--
## Setup Your Development Environment

We use [devcontainers](https://code.visualstudio.com/docs/devcontainers/containers) for development. To start your environment, either use Github Codespaces (click on "Code" -> "Codespaces" in Github to open one) as easiest way to get started, or [devpod](https://github.com/loft-sh/devpod) as open source alternative (directly pointing to our Kubernetes or your local docker installation).

Run `make` to get an overview of all commands that will setup a self-contained tira application in your dev environment.

1. Setup the database and compile the vuetify frontend
   ```bash
   ~$ make setup
   ```

2. Start the local environment, point your browser to the specified URL
   ```bash
   ~$ make run-develop
   ```

3. Optionally: To work on real data, initialize your development database from a database dump via
   ```bash
   ~$ make import-data-from-dump
   ```
   or to work with mock data run:
    ```bash
   ~$ cd application
   ~$ make import-mock-data
   ```

-->

## Citation

If you use TIRA in your own research, please cite our paper

```bibtex
@InProceedings{froebe:2023b,
  address =                  {Berlin Heidelberg New York},
  author =                   {Maik Fr{\"o}be and Matti Wiegmann and Nikolay Kolyada and Bastian Grahm and Theresa Elstner and Frank Loebe and Matthias Hagen and Benno Stein and Martin Potthast},
  booktitle =                {Advances in Information Retrieval. 45th European Conference on {IR} Research ({ECIR} 2023)},
  month =                    apr,
  publisher =                {Springer},
  series =                   {Lecture Notes in Computer Science},
  site =                     {Dublin, Irland},
  title =                    {{Continuous Integration for Reproducible Shared Tasks with TIRA.io}},
  todo =                     {doi, month, pages, code},
  year =                     2023
}
```
## License

[MIT License](LICENSE)
