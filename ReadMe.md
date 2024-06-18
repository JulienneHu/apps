# Guidance to Insatll and Setup XQuartz

- Vist https://www.xquartz.org/ to Install Qurtz

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


- In terminals

  

  ```bash
  docker build -t options .
  
  docker run -e DISPLAY=host.docker.internal:0 -e SCRIPT_NAME=pnl_new.py -v /tmp/.X11-unix:/tmp/.X11-unix -p 4000:80 options
   
  docker tag options junhuuu/options:latest
  
  docker push  junhuuu/options:latest 
  
  ```

<img src="/Users/julienne_hu/Library/Application Support/typora-user-images/image-20240616221806615.png" alt="image-20240616221806615" style="zoom:50%;" />

​	

dckr_pat_oRLP5mOMKKS_bDlWQXlK1Ka5Aos

