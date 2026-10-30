// SPDX-License-Identifier: Apache-2.0
package io.github.apdelrahman1911.nativecmpkit.verification.geoprobe;

import android.os.Bundle;
import android.widget.TextView;
import androidx.fragment.app.FragmentActivity;

/** Actual foreground lifecycle in a different UID/process from the test reporter. */
public final class GeoProbeActivity extends FragmentActivity {
    static GeoProbeActivity active;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TextView text = new TextView(this);
        text.setText("NativeCmpKit disposable foreground location verification");
        setContentView(text);
    }

    @Override public void onResume() { super.onResume(); active = this; }
    @Override public void onDestroy() {
        if (active == this) active = null;
        super.onDestroy();
    }
}
