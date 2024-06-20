# Part 1For Users to Run the Code(only steps)

- First Open docker, and in terminal

  ```bash
  docker login
  ```

  

- For MacOs Users, remember to have XQuartz Installed and Setup, make sure docker connection( See Part 2)

- Commands to Run

  ```
  # This works once you firstly open docker or you have some changes in github
  docker pull  junhuuu/options:latest 
  
  # change file name in the SCRIPT_NAME to run different files
  docker run -e DISPLAY=host.docker.internal:0 -e SCRIPT_NAME=pnl_new.py -v /tmp/.X11-unix:/tmp/.X11-unix -p 4000:80 junhuuu/options
  ```

  

  

# Part2 Guidance to Insatll and Setup XQuartz

- Vist https://www.xquartz.org/ to Install Quartz

- Configuration

  **Open XQuartz** and go to **XQuartz** -> **Preferences** in the menu bar.

  Click on the **Security** tab.

  Ensure **"Allow connections from network clients"** is checked.

  **Restart** XQuartz to apply the changes.

- Allow Docker to Connect to XQuartz

  In terminal

  ```bash
  xhost + 127.0.0.1
  ```

  In xquartz

  ```bash
  xhost 
  ```



# Part3 Some other Commands

```bash
docker build -t junhuuu/options .
docker build --no-cache -t junhuuu/options:latest .

docker pull  junhuuu/options:latest 

docker run -e DISPLAY=host.docker.internal:0 -e SCRIPT_NAME=pnl_new.py -v /tmp/.X11-unix:/tmp/.X11-unix -p 4000:80 junhuuu/options

docker run --rm -e DISPLAY=host.docker.internal:0 \
           -e SCRIPT_NAME=blackScholes.py \
           -v /tmp/.X11-unix:/tmp/.X11-unix \
           -v /Users/julienne_hu/Desktop/Option_Apps/trades.db:/app/trades.db \
           -p 4000:80 \
           --name options_app_new \
           junhuuu/options


docker tag options junhuuu/options:latest


docker push  junhuuu/options:latest 

# clean containers for updating
docker stop $(docker ps -a -q --filter ancestor=options)
docker rm $(docker ps -a -q --filter ancestor=options)

```

<img src="/Users/julienne_hu/Library/Application Support/typora-user-images/image-20240616221806615.png" alt="image-20240616221806615" style="zoom:50%;" />

​	

dckr_pat_oRLP5mOMKKS_bDlWQXlK1Ka5Aos

