package com.example.secondmonitor;

import android.app.Activity;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Rect;
import android.os.Bundle;
import android.view.MotionEvent;
import android.view.View;
import java.io.BufferedInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

public final class MainActivity extends Activity {
    private static final String SERVER = "http://127.0.0.1:5000";
    private MonitorView monitorView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        monitorView = new MonitorView(this);
        setContentView(monitorView);
        new Thread(this::readStream, "second-monitor-stream").start();
    }

    private void readStream() {
        while (!Thread.currentThread().isInterrupted()) {
            try {
                HttpURLConnection connection = (HttpURLConnection) new URL(SERVER + "/stream").openConnection();
                connection.setConnectTimeout(3000);
                connection.setReadTimeout(0);
                BufferedInputStream input = new BufferedInputStream(connection.getInputStream());
                readMultipartFrames(input);
            } catch (IOException ignored) {
                monitorView.setStatus("Waiting for USB stream. Run scripts/start-linux.sh on the laptop.");
                sleep(1000);
            }
        }
    }

    private void readMultipartFrames(BufferedInputStream input) throws IOException {
        ByteArrayOutputStream frame = new ByteArrayOutputStream();
        int previous = -1;
        int current;
        while ((current = input.read()) != -1) {
            if (previous == 0xff && current == 0xd8) {
                frame.reset();
                frame.write(0xff);
            }
            if (frame.size() > 0) {
                frame.write(current);
            }
            if (previous == 0xff && current == 0xd9) {
                byte[] data = frame.toByteArray();
                Bitmap bitmap = BitmapFactory.decodeByteArray(data, 0, data.length);
                if (bitmap != null) {
                    monitorView.setBitmap(bitmap);
                }
                frame.reset();
            }
            previous = current;
        }
    }

    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
        }
    }

    private static void sendTouch(float x, float y, int width, int height, String action) {
        new Thread(() -> {
            try {
                HttpURLConnection connection = (HttpURLConnection) new URL(SERVER + "/touch").openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(1000);
                connection.setReadTimeout(1000);
                connection.setRequestProperty("Content-Type", "application/json");
                connection.setDoOutput(true);
                String json = String.format(Locale.US,
                    "{\"x\":%.2f,\"y\":%.2f,\"width\":%d,\"height\":%d,\"action\":\"%s\"}",
                    x, y, width, height, action);
                byte[] body = json.getBytes(StandardCharsets.UTF_8);
                OutputStream output = connection.getOutputStream();
                output.write(body);
                output.close();
                connection.getInputStream().close();
            } catch (IOException ignored) {
            }
        }, "second-monitor-touch").start();
    }

    private static final class MonitorView extends View {
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private Bitmap bitmap;
        private String status = "Connect the tablet with USB debugging enabled.";

        MonitorView(Activity activity) {
            super(activity);
            setBackgroundColor(Color.BLACK);
        }

        void setBitmap(Bitmap nextBitmap) {
            post(() -> {
                bitmap = nextBitmap;
                status = null;
                invalidate();
            });
        }

        void setStatus(String nextStatus) {
            post(() -> {
                status = nextStatus;
                invalidate();
            });
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            if (bitmap != null) {
                canvas.drawBitmap(bitmap, null, new Rect(0, 0, getWidth(), getHeight()), paint);
                return;
            }
            paint.setColor(Color.WHITE);
            paint.setTextSize(42f);
            canvas.drawText("Second Monitor USB", 48f, 90f, paint);
            paint.setColor(Color.rgb(156, 163, 175));
            paint.setTextSize(26f);
            canvas.drawText(status, 48f, 145f, paint);
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            String action;
            if (event.getActionMasked() == MotionEvent.ACTION_UP) {
                action = "tap";
            } else if (event.getActionMasked() == MotionEvent.ACTION_MOVE || event.getActionMasked() == MotionEvent.ACTION_DOWN) {
                action = "move";
            } else {
                return true;
            }
            sendTouch(event.getX(), event.getY(), getWidth(), getHeight(), action);
            return true;
        }
    }
}
