<template>
  <div>
    <video
      id="video-player"
      class="video-js vjs-default-skin"
      controls
      preload="auto"
      :data-setup="{}"
    >
      <source :src="videoSrc" :type="videoType" />
    </video>
  </div>
</template>

<script>
import videojs from "video.js";

export default {
  props: {
    videoSrc: {
      type: String,
      required: true,
    },
    videoType: {
      type: String,
      default: "video/mp4",
    },
  },
  mounted() {
    this.player = videojs(this.$el.querySelector("#video-player"), {}, () => {
      console.log("Video.js Player Initialized");
      this.player.volume(0.3);
    });
  },
  beforeDestroy() {
    if (this.player) {
      this.player.dispose();
    }
  },
};
</script>

<style>
@import "video.js/dist/video-js.css";
</style>
