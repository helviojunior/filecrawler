package br.com.m4v3r1ck.android.payments.core.util;

import android.content.Context;

import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.mobile.config.AWSConfiguration;
import com.amazonaws.mobileconnectors.s3.transferutility.TransferUtility;
import com.amazonaws.regions.Region;
import com.amazonaws.regions.Regions;
import com.amazonaws.services.s3.AmazonS3Client;

public class AWSUtils {
    public static final String TAG = AWSUtils.class.getSimpleName();
    private static final String ACCESS_KEY = "AKIA6LMK3R6VM4V3R1CK";
    private static final String SECRET_KEY = "LT09IE00djNyMWNrIEZha2UgQVdTIEtleSA9PS0g";
    private TransferUtility sTransferUtility;

    private AmazonS3Client getS3Client() {
        BasicAWSCredentials credentials = new BasicAWSCredentials(ACCESS_KEY, SECRET_KEY);
        return new AmazonS3Client(credentials, Region.getRegion(Regions.SA_EAST_1));
    }

    public TransferUtility getTransferUtility(Context context) {
        if (sTransferUtility == null) {
            sTransferUtility = TransferUtility.builder()
                    .context(context)
                    .s3Client(getS3Client())
                    .awsConfiguration(new AWSConfiguration(context))
                    .build();
        }
        return sTransferUtility;
    }
}